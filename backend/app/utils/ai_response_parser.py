"""Unified AI response parser for extracting structured data from LLM outputs.

The core problem: LLMs return varied formats — JSON in markdown, plain text with
headers, mixed formats, wrong schema, partial JSON, etc. Every generator had its
own fragile regex parser that broke in different ways.

This module provides a single robust parser that tries MULTIPLE extraction
strategies in order of reliability:

  1. Clean JSON extraction (code blocks, raw JSON, bracket matching)
  2. JSON repair (trailing commas, single quotes, unquoted keys)
  3. Multiple-JSON extraction (AI returns several JSON objects in sequence)
  4. XML tag extraction (<item><name>...</name>...</item>)
  5. XML+JSON hybrid (<item>{...json...}</item>)
  6. Field-by-field text extraction (regex for "Field: value" patterns)
  7. Bold-header section splitting (**Name** followed by content)
  8. Numbered section splitting (1. Name\n  Description: ...)

Each strategy feeds into the same validation/coercion pipeline, so the
downstream code always gets clean, typed dicts regardless of how messy the
AI response was.

The schema system is **format-agnostic**: the same ResponseSchema can generate
prompt instructions in JSON, XML, or hybrid (XML wrapping JSON) format via
OutputFormat. This lets you A/B test which format a given model handles best.
"""

import json
import re
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger("infinite_story.utils.ai_response_parser")


# ---------------------------------------------------------------------------
# Output format enum
# ---------------------------------------------------------------------------

class OutputFormat(Enum):
    """Controls how prompt instructions and parsing strategies are selected.

    JSON:       Classic JSON objects / arrays.  Best for structured data.
    XML:        XML-style tags (<item><name>...</name></item>).
                Some models produce cleaner structured output with XML because
                the tags act as explicit delimiters.
    XML_JSON:   Hybrid — XML wrapper tags around JSON payloads.
                e.g. <faction>{"name": "...", ...}</faction>
                Combines the delimiter clarity of XML with the type-richness
                of JSON.  Good middle ground for testing.
    """
    JSON = "json"
    XML = "xml"
    XML_JSON = "xml_json"


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

@dataclass
class FieldSpec:
    """Specification for a single field in an expected response.

    Attributes:
        name: Field name in the JSON
        type: Expected type ("str", "int", "float", "list", "dict", "bool")
        required: Whether this field is critical (used for quality scoring)
        default: Default value if missing
        aliases: Alternative field names the AI might use (case-insensitive)
        coerce: If True, attempt type coercion (e.g., "42" -> 42 for int)
    """
    name: str
    type: str = "str"
    required: bool = False
    default: Any = None
    aliases: List[str] = field(default_factory=list)
    coerce: bool = True


@dataclass
class ResponseSchema:
    """Schema describing expected AI response structure.

    Attributes:
        fields: List of field specifications
        expect_array: If True, expect multiple items (e.g., 3 factions)
        min_items: Minimum items expected in array mode
        max_items: Maximum items expected in array mode
        item_tag: XML tag name for each item (used in XML/hybrid formats).
                  Defaults to "item". Use something semantic like "faction",
                  "location", "character" for clearer prompts.
        root_tag: XML tag name for the root wrapper (array mode).
                  Defaults to "items".
    """
    fields: List[FieldSpec]
    expect_array: bool = False
    min_items: int = 1
    max_items: int = 20
    item_tag: str = "item"
    root_tag: str = "items"


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

class AIResponseParser:
    """Parse and validate AI responses against a schema.

    Usage:
        schema = ResponseSchema(
            fields=[
                FieldSpec("name", required=True),
                FieldSpec("description"),
                FieldSpec("goals", type="list"),
            ],
            expect_array=True,
            min_items=3,
        )
        results = AIResponseParser.parse(ai_text, schema, fallback_defaults=[...])
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def parse(
        cls,
        text: str,
        schema: ResponseSchema,
        fallback_defaults: Optional[List[dict]] = None,
        preferred_format: Optional[OutputFormat] = None,
    ) -> List[dict]:
        """Parse an AI response into a list of validated objects.

        Tries multiple extraction strategies, picks the best result, then
        pads/trims to meet min/max item counts.

        The parser is format-agnostic: it always runs ALL strategies regardless
        of preferred_format.  The preferred_format only affects priority ordering
        (strategies matching the expected format are tried first and get a small
        scoring bonus).  This way even if the AI returns a different format than
        asked for, we still parse it correctly.

        Args:
            text: Raw AI response text (may include markdown, preamble, etc.)
            schema: Expected response structure
            fallback_defaults: Default items if parsing completely fails
            preferred_format: If set, strategies matching this format get
                              priority.  Does NOT disable other strategies.

        Returns:
            List of validated dicts, one per item.
        """
        if fallback_defaults is None:
            fallback_defaults = []

        if not text or not text.strip():
            logger.warning("Empty AI response text")
            return fallback_defaults

        # Build the strategy list with labels for logging
        strategies = [
            ("json",              cls._strategy_json),
            ("multi_json",        cls._strategy_multi_json),
            ("xml",               cls._strategy_xml),
            ("xml_json_hybrid",   cls._strategy_xml_json_hybrid),
            ("bold_sections",     cls._strategy_bold_sections),
            ("numbered_sections", cls._strategy_numbered_sections),
            ("heading_sections",  cls._strategy_heading_sections),
        ]

        # If a preferred format is given, put matching strategies first
        if preferred_format == OutputFormat.XML:
            strategies = cls._reorder_strategies(strategies, prefer=["xml"])
        elif preferred_format == OutputFormat.XML_JSON:
            strategies = cls._reorder_strategies(strategies, prefer=["xml_json_hybrid", "xml"])
        elif preferred_format == OutputFormat.JSON:
            strategies = cls._reorder_strategies(strategies, prefer=["json", "multi_json"])

        # Collect candidates from all strategies
        all_candidates: List[List[dict]] = []

        for label, strategy_fn in strategies:
            items = strategy_fn(text, schema)
            if items:
                all_candidates.append(items)
                logger.debug(f"Strategy {label}: {len(items)} items")

        # Pick the best candidate set
        best = cls._pick_best(all_candidates, schema)

        if not best:
            logger.warning("All parsing strategies failed, using fallback defaults")
            return fallback_defaults

        # Pad with defaults if not enough items
        if schema.expect_array and len(best) < schema.min_items:
            logger.info(
                f"Parsed {len(best)} items, padding to {schema.min_items} with defaults"
            )
            for i in range(len(best), schema.min_items):
                if i < len(fallback_defaults):
                    best.append(fallback_defaults[i])
                elif fallback_defaults:
                    # Cycle through defaults if we run out
                    best.append(fallback_defaults[i % len(fallback_defaults)])

        # Trim to max
        if schema.max_items and len(best) > schema.max_items:
            best = best[:schema.max_items]

        return best

    @staticmethod
    def _reorder_strategies(strategies, prefer: List[str]):
        """Move preferred strategies to the front of the list."""
        preferred = []
        rest = []
        prefer_set = set(prefer)
        for s in strategies:
            if s[0] in prefer_set:
                preferred.append(s)
            else:
                rest.append(s)
        return preferred + rest

    # ------------------------------------------------------------------
    # Strategy 1: JSON extraction (handles code blocks, raw JSON, repair)
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_json(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Try to extract valid JSON and map it to schema items."""
        parsed = cls._extract_json(text)
        if parsed is None:
            # Try repairing common JSON issues
            parsed = cls._extract_json_repaired(text)
        if parsed is None:
            return []
        return cls._json_to_items(parsed, schema)

    @staticmethod
    def _extract_json(text: str) -> Optional[Union[dict, list]]:
        """Extract JSON from text, trying multiple approaches."""
        # 1. Markdown code block
        code_block = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?\s*```', text)
        if code_block:
            try:
                return json.loads(code_block.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 2. Raw text as JSON
        stripped = text.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

        # 3. Bracket matching for outermost JSON structure
        for opener, closer in [('{', '}'), ('[', ']')]:
            start = stripped.find(opener)
            if start == -1:
                continue
            depth = 0
            in_str = False
            esc = False
            for i in range(start, len(stripped)):
                c = stripped[i]
                if esc:
                    esc = False
                    continue
                if c == '\\' and in_str:
                    esc = True
                    continue
                if c == '"' and not esc:
                    in_str = not in_str
                    continue
                if in_str:
                    continue
                if c == opener:
                    depth += 1
                elif c == closer:
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(stripped[start:i + 1])
                        except json.JSONDecodeError:
                            break
        return None

    @staticmethod
    def _extract_json_repaired(text: str) -> Optional[Union[dict, list]]:
        """Try to repair common JSON problems and re-parse.

        Fixes: trailing commas, single quotes, unquoted keys, // comments.
        """
        # Get content from code block or whole text
        code_block = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?\s*```', text)
        raw = code_block.group(1).strip() if code_block else text.strip()

        # Find the outermost braces/brackets
        start = -1
        for i, c in enumerate(raw):
            if c in ('{', '['):
                start = i
                break
        if start == -1:
            return None

        # Take from first brace to end
        raw = raw[start:]

        # Remove // comments
        raw = re.sub(r'//[^\n]*', '', raw)
        # Remove trailing commas before } or ]
        raw = re.sub(r',\s*([}\]])', r'\1', raw)
        # Replace single quotes with double quotes (careful with apostrophes)
        # Only do this if there are no double quotes at all
        if '"' not in raw and "'" in raw:
            raw = raw.replace("'", '"')

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    @classmethod
    def _json_to_items(cls, parsed: Union[dict, list], schema: ResponseSchema) -> List[dict]:
        """Convert parsed JSON (object or array) into a list of schema-validated items."""
        items = []

        if isinstance(parsed, list):
            for obj in parsed:
                if isinstance(obj, dict):
                    items.append(cls._validate_object(obj, schema))
            return items

        if not isinstance(parsed, dict):
            return []

        # Check if this object IS one of our items (single-item response)
        if cls._looks_like_item(parsed, schema):
            return [cls._validate_object(parsed, schema)]

        # Look for an array field inside the object
        _ARRAY_KEYS = [
            'items', 'results', 'data',
            'factions', 'locations', 'characters', 'arcs', 'story_arcs',
            'systems', 'magic_systems', 'episodes', 'choices',
        ]
        for key in _ARRAY_KEYS:
            if key in parsed and isinstance(parsed[key], list):
                for obj in parsed[key]:
                    if isinstance(obj, dict):
                        items.append(cls._validate_object(obj, schema))
                if items:
                    return items

        # Look for indexed keys: "arc_1", "faction_1", "1", "2", etc.
        indexed = {}
        for k, v in parsed.items():
            if isinstance(v, dict):
                # Try to extract a sort key
                m = re.search(r'(\d+)', k)
                sort_key = int(m.group(1)) if m else hash(k)
                indexed[sort_key] = v
        if len(indexed) >= 2:
            for k in sorted(indexed.keys()):
                items.append(cls._validate_object(indexed[k], schema))
            return items

        # Last resort: treat the whole object as a single item
        return [cls._validate_object(parsed, schema)]

    # ------------------------------------------------------------------
    # Strategy 2: Multiple JSON objects in sequence
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_multi_json(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Handle AI responses that contain multiple separate JSON objects."""
        if not schema.expect_array:
            return []

        items = []
        # Find all top-level JSON objects (not nested)
        for m in re.finditer(r'\{', text):
            start = m.start()
            depth = 0
            in_str = False
            esc = False
            for i in range(start, len(text)):
                c = text[i]
                if esc:
                    esc = False
                    continue
                if c == '\\' and in_str:
                    esc = True
                    continue
                if c == '"' and not esc:
                    in_str = not in_str
                    continue
                if in_str:
                    continue
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i + 1]
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict) and cls._looks_like_item(obj, schema):
                                items.append(cls._validate_object(obj, schema))
                        except json.JSONDecodeError:
                            pass
                        break

        # Only return if we found multiple objects (otherwise strategy 1 handles it)
        return items if len(items) >= 2 else []

    # ------------------------------------------------------------------
    # Strategy 3: XML tag extraction
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_xml(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Extract data from XML-style tagged responses.

        Handles responses like:
            <faction>
              <name>The Iron Conclave</name>
              <description>A militaristic guild...</description>
              <goals>
                <goal>Control trade routes</goal>
                <goal>Expand territory</goal>
              </goals>
            </faction>

        Also handles self-closing and attribute-based patterns.
        """
        items = []

        # Determine which wrapper tags to look for
        item_tags = cls._get_xml_item_tags(schema)

        for tag in item_tags:
            # Find all <tag>...</tag> blocks (non-greedy, handles nesting)
            blocks = cls._extract_xml_blocks(text, tag)
            for block_content in blocks:
                # If the inner content is JSON, skip (handled by xml_json strategy)
                stripped = block_content.strip()
                if stripped.startswith('{') or stripped.startswith('['):
                    continue

                item = cls._parse_xml_fields(block_content, schema)
                if item and any(v for v in item.values() if v and v != [] and v != {}):
                    items.append(item)

        return items

    @classmethod
    def _get_xml_item_tags(cls, schema: ResponseSchema) -> List[str]:
        """Determine plausible XML tag names for items based on schema."""
        tags = [schema.item_tag]
        # Also try common variations
        if schema.item_tag != "item":
            tags.append("item")
        # Try the root_tag singular form
        singular = schema.root_tag.rstrip('s')
        if singular and singular not in tags:
            tags.append(singular)
        return tags

    @classmethod
    def _extract_xml_blocks(cls, text: str, tag: str) -> List[str]:
        """Extract all <tag>...</tag> content blocks from text.

        Handles nested same-name tags correctly using depth counting.
        """
        blocks = []
        opener = f'<{tag}'  # might have attributes: <faction id="1">
        closer = f'</{tag}>'

        pos = 0
        while pos < len(text):
            # Find opening tag (with optional attributes)
            match = re.search(
                rf'<{re.escape(tag)}(?:\s[^>]*)?>',
                text[pos:],
                re.IGNORECASE,
            )
            if not match:
                break

            start = pos + match.end()  # content starts after >
            tag_start = pos + match.start()

            # Count depth to handle nested same-name tags
            depth = 1
            search_pos = start
            while depth > 0 and search_pos < len(text):
                next_open = re.search(
                    rf'<{re.escape(tag)}(?:\s[^>]*)?>',
                    text[search_pos:],
                    re.IGNORECASE,
                )
                next_close = re.search(
                    rf'</{re.escape(tag)}\s*>',
                    text[search_pos:],
                    re.IGNORECASE,
                )

                if next_close is None:
                    break

                # If there's an open before the close, increase depth
                if next_open and next_open.start() < next_close.start():
                    depth += 1
                    search_pos += next_open.end()
                else:
                    depth -= 1
                    if depth == 0:
                        end = search_pos + next_close.start()
                        blocks.append(text[start:end])
                    search_pos += next_close.end()

            pos = search_pos if search_pos > tag_start + 1 else tag_start + 1

        return blocks

    @classmethod
    def _parse_xml_fields(cls, xml_content: str, schema: ResponseSchema) -> dict:
        """Parse field values from XML content.

        For each schema field, look for <field_name>value</field_name>.
        For list fields, collect multiple child elements.
        """
        item = {}

        for field_spec in schema.fields:
            # Try primary name + aliases as tag names
            tag_names = [field_spec.name] + field_spec.aliases
            # Also try hyphenated versions: what_it_can_do -> what-it-can-do
            for name in list(tag_names):
                hyphenated = name.replace('_', '-')
                if hyphenated != name and hyphenated not in tag_names:
                    tag_names.append(hyphenated)
                # CamelCase: what_it_can_do -> whatItCanDo
                parts = name.split('_')
                if len(parts) > 1:
                    camel = parts[0] + ''.join(p.capitalize() for p in parts[1:])
                    if camel not in tag_names:
                        tag_names.append(camel)

            value = None

            for tag_name in tag_names:
                if field_spec.type == "list":
                    value = cls._extract_xml_list(xml_content, tag_name, field_spec)
                    if value:
                        break
                else:
                    value = cls._extract_xml_value(xml_content, tag_name)
                    if value is not None:
                        break

            if value is not None:
                if field_spec.coerce:
                    item[field_spec.name] = cls._coerce_value(value, field_spec.type)
                else:
                    item[field_spec.name] = value
            else:
                # Apply default
                if field_spec.default is not None:
                    item[field_spec.name] = field_spec.default
                elif field_spec.type == "list":
                    item[field_spec.name] = []
                elif field_spec.type == "dict":
                    item[field_spec.name] = {}
                elif field_spec.type == "str":
                    item[field_spec.name] = ""

        return item

    @staticmethod
    def _extract_xml_value(xml_content: str, tag_name: str) -> Optional[str]:
        """Extract a single value from <tag_name>value</tag_name>."""
        pattern = rf'<{re.escape(tag_name)}(?:\s[^>]*)?>([\s\S]*?)</{re.escape(tag_name)}\s*>'
        m = re.search(pattern, xml_content, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            # Strip inner tags if the value contains only text
            if '<' not in value:
                return value
            # If it has inner tags, return raw (might be nested structure)
            return value
        return None

    @classmethod
    def _extract_xml_list(cls, xml_content: str, tag_name: str, field_spec: FieldSpec) -> Optional[List[str]]:
        """Extract a list field from XML.

        Handles multiple patterns:
        1. Wrapper tag with child elements:
           <goals><goal>A</goal><goal>B</goal></goals>
        2. Wrapper with differently-named children (auto-discovered):
           <what_it_can_do><capability>X</capability></what_it_can_do>
        3. Repeated sibling elements:
           <goal>A</goal><goal>B</goal>
        4. Wrapper with plain text (comma/newline separated)
        """
        # Build list of wrapper tag names to try (the field name + its aliases)
        all_tag_names = [tag_name]
        # Also try hyphenated/camel versions
        hyphenated = tag_name.replace('_', '-')
        if hyphenated != tag_name:
            all_tag_names.append(hyphenated)

        for wrapper in all_tag_names:
            wrapper_content = cls._extract_xml_value(xml_content, wrapper)
            if not wrapper_content:
                continue

            if '<' in wrapper_content:
                # Has child tags — try to extract them

                # Strategy A: try singular of wrapper as child tag
                child_candidates = []
                singular = wrapper.rstrip('s') if wrapper.endswith('s') and wrapper != wrapper.rstrip('s') else None
                if singular:
                    child_candidates.append(singular)

                # Strategy B: try generic child tags
                child_candidates.extend(['li', 'item', 'entry', 'value'])

                # Strategy C: auto-discover child tags from content
                # Find all opening tags in the wrapper content
                discovered = re.findall(r'<([a-zA-Z_][a-zA-Z0-9_-]*)\s*[^>]*>', wrapper_content)
                # Filter out closing-tag artifacts and deduplicate while preserving order
                seen = set()
                for d in discovered:
                    dl = d.lower()
                    if dl not in seen:
                        seen.add(dl)
                        child_candidates.append(d)

                for child_tag in child_candidates:
                    children = re.findall(
                        rf'<{re.escape(child_tag)}(?:\s[^>]*)?>([\s\S]*?)</{re.escape(child_tag)}\s*>',
                        wrapper_content,
                        re.IGNORECASE,
                    )
                    if children:
                        return [c.strip() for c in children if c.strip()]
            else:
                # Plain text inside wrapper — try splitting
                if ',' in wrapper_content:
                    items = [s.strip() for s in wrapper_content.split(',') if s.strip()]
                    if items:
                        return items
                if '\n' in wrapper_content:
                    lines = []
                    for line in wrapper_content.split('\n'):
                        line = re.sub(r'^[-•*]\s*|^\d+[\.\)]\s*', '', line).strip()
                        if line:
                            lines.append(line)
                    if lines:
                        return lines

        # Pattern: Direct repeated sibling elements (no wrapper)
        singular = tag_name.rstrip('s') if tag_name.endswith('s') and tag_name != tag_name.rstrip('s') else tag_name
        for attempt_tag in ([singular, tag_name] if singular != tag_name else [tag_name]):
            matches = re.findall(
                rf'<{re.escape(attempt_tag)}(?:\s[^>]*)?>([\s\S]*?)</{re.escape(attempt_tag)}\s*>',
                xml_content,
                re.IGNORECASE,
            )
            if len(matches) >= 2:
                return [m.strip() for m in matches if m.strip()]

        return None

    # ------------------------------------------------------------------
    # Strategy 4: XML + JSON hybrid
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_xml_json_hybrid(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Extract data from XML tags wrapping JSON payloads.

        Handles responses like:
            <faction>
            {"name": "The Iron Conclave", "description": "...", "goals": [...]}
            </faction>
            <faction>
            {"name": "The Silk Court", "description": "...", "goals": [...]}
            </faction>
        """
        items = []
        item_tags = cls._get_xml_item_tags(schema)

        for tag in item_tags:
            blocks = cls._extract_xml_blocks(text, tag)
            for block_content in blocks:
                stripped = block_content.strip()

                # Try parsing the inner content as JSON
                parsed = cls._extract_json(stripped)
                if parsed is None:
                    parsed = cls._extract_json_repaired(stripped)
                if parsed is None:
                    continue

                if isinstance(parsed, dict):
                    items.append(cls._validate_object(parsed, schema))
                elif isinstance(parsed, list):
                    for obj in parsed:
                        if isinstance(obj, dict):
                            items.append(cls._validate_object(obj, schema))

        return items

    # ------------------------------------------------------------------
    # Strategy 5: Bold-header sections (**Name** + content) [was 3]
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_bold_sections(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Split text by **bold** headers and extract fields from each section."""
        # Split on **header** patterns
        parts = re.split(r'\*\*([^*]+)\*\*', text)
        # parts alternates: [preamble, header1, content1, header2, content2, ...]

        if len(parts) < 3:
            return []

        # Known template headers to skip
        _SKIP = {
            'faction name', 'faction', 'name', 'description', 'goals', 'goal',
            'leader', 'resources', 'alignment', 'opposition', 'rivalry',
            'system name', 'magic system', 'tech system', 'location name',
            'important', 'note', 'notes', 'instructions', 'example',
            'arc name', 'character name',
        }

        items = []
        for i in range(1, len(parts), 2):
            header = parts[i].strip().rstrip(':')
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""

            # Skip template headers and very short headers
            if header.lower() in _SKIP or len(header) < 2:
                continue
            # Skip headers that look like field labels
            if re.match(r'^(Description|Goals?|Leader|Resources?|Alignment|What It|Costs?|Limitations?|Short|Full|Connections?|Importance|Premise|Conflict|Themes?|Direction|Mysteries|Hooks?)\b', header, re.IGNORECASE):
                continue

            item = cls._extract_fields_from_text(content, schema)
            # Use the bold header as the name field
            if 'name' in [f.name for f in schema.fields]:
                item['name'] = header
            elif 'title' in [f.name for f in schema.fields] and not item.get('title'):
                item['title'] = header

            # Only keep if we got at least the header
            if item:
                items.append(item)

        return items

    # ------------------------------------------------------------------
    # Strategy 6: Numbered sections [was 4]
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_numbered_sections(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Split text by numbered items (1. ... 2. ... etc.)."""
        # Split on lines that start with a number followed by . or )
        sections = re.split(r'\n(?=\d+[\.\)]\s+)', text)

        items = []
        for section in sections:
            section = section.strip()
            if not section or len(section) < 15:
                continue

            # Check if this section starts with a number
            m = re.match(r'^\d+[\.\)]\s+(.+?)(?:\n|$)', section)
            if not m:
                continue

            first_line = m.group(1).strip()
            # Clean up the header: remove bold, trailing colon
            header = re.sub(r'\*\*([^*]+)\*\*', r'\1', first_line).rstrip(':').strip()

            item = cls._extract_fields_from_text(section, schema)
            if 'name' in [f.name for f in schema.fields] and not item.get('name'):
                item['name'] = header
            elif 'title' in [f.name for f in schema.fields] and not item.get('title'):
                item['title'] = header

            if item:
                items.append(item)

        return items

    # ------------------------------------------------------------------
    # Strategy 7: Heading sections (### Name) [was 5]
    # ------------------------------------------------------------------

    @classmethod
    def _strategy_heading_sections(cls, text: str, schema: ResponseSchema) -> List[dict]:
        """Split text by markdown headings (## or ###)."""
        sections = re.split(r'\n(?=#{2,3}\s+)', text)

        items = []
        for section in sections:
            section = section.strip()
            m = re.match(r'^#{2,3}\s+(.+?)(?:\n|$)', section)
            if not m:
                continue

            header = m.group(1).strip().rstrip(':')
            item = cls._extract_fields_from_text(section, schema)
            if 'name' in [f.name for f in schema.fields] and not item.get('name'):
                item['name'] = header
            elif 'title' in [f.name for f in schema.fields] and not item.get('title'):
                item['title'] = header

            if item:
                items.append(item)

        return items

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @classmethod
    def _name_to_label_patterns(cls, name: str) -> List[str]:
        """Convert a field name or alias to possible text label forms.

        "capabilities"        -> ["capabilities"]
        "what_it_can_do"      -> ["what_it_can_do", "what it can do"]
        "costs_and_consequences" -> ["costs_and_consequences", "costs and consequences", "costs & consequences"]
        "central_conflict"    -> ["central_conflict", "central conflict"]
        """
        patterns = [name]
        # underscore -> space version
        spaced = name.replace('_', ' ')
        if spaced != name:
            patterns.append(spaced)
            # Also try "and" -> "&"
            if ' and ' in spaced:
                patterns.append(spaced.replace(' and ', ' & '))
            if ' or ' in spaced:
                patterns.append(spaced.replace(' or ', ' / '))
        return patterns

    @classmethod
    def _extract_fields_from_text(cls, text: str, schema: ResponseSchema) -> dict:
        """Extract field values from a block of text using multiple patterns.

        Tries each field with many regex strategies:
        1. Exact label match: "Field Name: value"
        2. Bold label: "**Field Name**: value" or "- **Field Name**: value"
        3. Parenthesized label: "Field Name (details): value"
        4. Multi-line list items after the label
        5. Comma-separated values on the same line
        """
        item = {}

        for field_spec in schema.fields:
            # Build all possible text labels for this field
            raw_names = [field_spec.name] + field_spec.aliases
            search_labels = []
            for rn in raw_names:
                search_labels.extend(cls._name_to_label_patterns(rn))
            # Deduplicate while preserving order
            seen = set()
            unique_labels = []
            for lbl in search_labels:
                if lbl.lower() not in seen:
                    seen.add(lbl.lower())
                    unique_labels.append(lbl)

            value = None

            for label in unique_labels:
                escaped = re.escape(label)
                # Allow optional parenthesized content after the label
                # e.g., "What It Can Do (2-3 capabilities):"
                label_pattern = rf'{escaped}(?:\s*\([^)]*\))?'

                # Pattern 1: "Field: value" or "- Field: value"
                m = re.search(
                    rf'(?:^|\n)\s*[-•*]?\s*(?:\*\*)?{label_pattern}(?:\*\*)?\s*[:—]\s*(.+?)(?:\n|$)',
                    text, re.IGNORECASE
                )
                if m:
                    value = m.group(1).strip().rstrip(',')
                    break

                # Pattern 2: "**Field**: value"
                m = re.search(
                    rf'\*\*{label_pattern}\*\*\s*[:—]\s*(.+?)(?:\n|$)',
                    text, re.IGNORECASE
                )
                if m:
                    value = m.group(1).strip().rstrip(',')
                    break

                # Pattern 3: Label at start of line with no colon, but followed by content
                # e.g., "TITLE The Awakening"
                m = re.search(
                    rf'(?:^|\n)\s*{escaped}\s+([A-Z][^\n]+?)(?:\n|$)',
                    text, re.IGNORECASE
                )
                if m and field_spec.type == "str":
                    value = m.group(1).strip()
                    break

            # For list fields, try harder — collect multi-line items
            if field_spec.type == "list":
                for label in unique_labels:
                    escaped = re.escape(label)
                    label_pattern = rf'{escaped}(?:\s*\([^)]*\))?'

                    # Find the label and grab everything until the next section
                    m = re.search(
                        rf'(?:^|\n)\s*[-•*]?\s*(?:\*\*)?{label_pattern}(?:\*\*)?\s*[:—]\s*([\s\S]*?)(?:\n\s*\n|\n(?=[-•*]?\s*(?:\*\*)?[A-Z][a-z]+(?:\s+[A-Z])?[^a-z]*[:—])|\Z)',
                        text, re.IGNORECASE
                    )
                    if m:
                        block = m.group(1).strip()
                        lines = []
                        for line in block.split('\n'):
                            line = line.strip()
                            line = re.sub(r'^[-•*]\s*|^\d+[\.\)]\s*', '', line).strip()
                            if line and len(line) > 2:
                                lines.append(line.rstrip('.,;'))
                        if lines:
                            value = lines
                            break

                # If we got a single string value for a list, try splitting
                if isinstance(value, str):
                    if ',' in value:
                        value = [s.strip() for s in value.split(',') if s.strip() and len(s.strip()) > 2]
                    elif value:
                        value = [value]

            if value is not None:
                if field_spec.coerce:
                    item[field_spec.name] = cls._coerce_value(value, field_spec.type)
                else:
                    item[field_spec.name] = value
            else:
                # Apply default
                if field_spec.default is not None:
                    item[field_spec.name] = field_spec.default
                elif field_spec.type == "list":
                    item[field_spec.name] = []
                elif field_spec.type == "dict":
                    item[field_spec.name] = {}
                elif field_spec.type == "str":
                    item[field_spec.name] = ""

        return item

    @classmethod
    def _validate_object(cls, data: dict, schema: ResponseSchema) -> dict:
        """Validate a JSON dict against the schema — resolve aliases and coerce types."""
        result = {}

        for field_spec in schema.fields:
            # Try primary name
            value = data.get(field_spec.name)

            # Try aliases (case-insensitive key matching)
            if value is None:
                for alias in field_spec.aliases:
                    value = data.get(alias)
                    if value is not None:
                        break

            # Case-insensitive key search as last resort
            if value is None:
                lower_name = field_spec.name.lower()
                alias_lowers = [a.lower() for a in field_spec.aliases]
                for k, v in data.items():
                    kl = k.lower().replace(' ', '_').replace('-', '_')
                    if kl == lower_name or kl in alias_lowers:
                        value = v
                        break

            # Apply default
            if value is None:
                if field_spec.default is not None:
                    result[field_spec.name] = field_spec.default
                elif field_spec.type == "list":
                    result[field_spec.name] = []
                elif field_spec.type == "dict":
                    result[field_spec.name] = {}
                elif field_spec.type == "str":
                    result[field_spec.name] = ""
                else:
                    result[field_spec.name] = None
                continue

            # Coerce
            if field_spec.coerce:
                value = cls._coerce_value(value, field_spec.type)

            result[field_spec.name] = value

        return result

    @classmethod
    def _looks_like_item(cls, obj: dict, schema: ResponseSchema) -> bool:
        """Check if a dict looks like one of our expected items (vs. a wrapper)."""
        if not schema.fields:
            return True

        # Count how many schema field names (or aliases) appear in the object keys
        obj_keys_lower = {k.lower().replace(' ', '_').replace('-', '_') for k in obj.keys()}
        matches = 0
        for f in schema.fields:
            names = [f.name.lower()] + [a.lower() for a in f.aliases]
            if any(n in obj_keys_lower for n in names):
                matches += 1

        # If at least 30% of schema fields match, it's probably an item
        threshold = max(1, len(schema.fields) * 0.3)
        return matches >= threshold

    @staticmethod
    def _coerce_value(value: Any, target_type: str) -> Any:
        """Coerce a value to the target type with aggressive fallbacks."""
        if value is None:
            return None

        if target_type == "str":
            if isinstance(value, str):
                return value
            if isinstance(value, (list, dict)):
                return json.dumps(value) if len(str(value)) < 500 else str(value)[:500]
            return str(value)

        if target_type == "int":
            if isinstance(value, int) and not isinstance(value, bool):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                nums = re.findall(r'\d+', value)
                return int(nums[0]) if nums else None
            return None

        if target_type == "float":
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(re.sub(r'[^\d.+-]', '', value))
                except (ValueError, TypeError):
                    return None
            return None

        if target_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower().strip() in ("true", "yes", "1", "on")
            return bool(value)

        if target_type == "list":
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                # Try JSON array first
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    pass
                # Split by common delimiters
                if '\n' in value:
                    items = []
                    for line in value.split('\n'):
                        line = re.sub(r'^[-•*]\s*|^\d+[\.\)]\s*', '', line).strip()
                        if line:
                            items.append(line)
                    return items if items else [value]
                if ',' in value:
                    return [s.strip() for s in value.split(',') if s.strip()]
                if ';' in value:
                    return [s.strip() for s in value.split(';') if s.strip()]
                return [value]
            if isinstance(value, dict):
                return list(value.values())
            return [value]

        if target_type == "dict":
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict):
                        return parsed
                except (json.JSONDecodeError, ValueError):
                    pass
            return None

        return value

    @classmethod
    def _pick_best(cls, candidates: List[List[dict]], schema: ResponseSchema) -> Optional[List[dict]]:
        """Pick the best result set from multiple extraction strategies.

        Scoring:
        - More items closer to min_items = better (for array mode)
        - More required fields filled = better
        - More total non-empty fields = better
        """
        if not candidates:
            return None

        def score(items: List[dict]) -> float:
            if not items:
                return -1

            s = 0.0

            # Item count score (for array mode)
            if schema.expect_array:
                if len(items) >= schema.min_items:
                    s += 100  # Big bonus for meeting minimum
                s += min(len(items), schema.min_items) * 10

            # Field quality score
            required_names = {f.name for f in schema.fields if f.required}
            all_names = {f.name for f in schema.fields}

            for item in items:
                for key, val in item.items():
                    if key not in all_names:
                        continue
                    if val is None or val == "" or val == []:
                        continue
                    if key in required_names:
                        s += 5  # Required field filled
                    else:
                        s += 1  # Optional field filled

            return s

        best = max(candidates, key=score)
        if score(best) <= 0:
            return None
        return best

    # ------------------------------------------------------------------
    # Prompt helpers — format-agnostic
    # ------------------------------------------------------------------

    @classmethod
    def get_prompt_instruction(
        cls,
        schema: ResponseSchema,
        fmt: OutputFormat = OutputFormat.JSON,
        example: Optional[dict] = None,
    ) -> str:
        """Generate format-specific prompt instructions for the AI.

        This is the main entry point.  Dispatches to the appropriate
        builder based on `fmt`.

        Args:
            schema: The response schema
            fmt: Desired output format (JSON, XML, or XML_JSON hybrid)
            example: Optional example dict to show the AI

        Returns:
            A prompt instruction string to append to the system/user prompt.
        """
        if fmt == OutputFormat.JSON:
            return cls.get_json_prompt_instruction(schema, example)
        elif fmt == OutputFormat.XML:
            return cls.get_xml_prompt_instruction(schema, example)
        elif fmt == OutputFormat.XML_JSON:
            return cls.get_xml_json_prompt_instruction(schema, example)
        else:
            return cls.get_json_prompt_instruction(schema, example)

    @staticmethod
    def get_json_prompt_instruction(
        schema: ResponseSchema,
        example: Optional[dict] = None,
    ) -> str:
        """Generate a prompt instruction telling the AI exactly what JSON to return.

        Produces a clear schema description + example that dramatically improves
        JSON parsing success rates.
        """
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array of strings",
            "dict": "object",
        }

        lines = []
        if schema.expect_array:
            lines.append(f"Return a JSON array of {schema.min_items} objects.")
            lines.append("Each object must have these fields:")
        else:
            lines.append("Return a single JSON object with these fields:")

        for f in schema.fields:
            type_label = type_map.get(f.type, f.type)
            req = "(REQUIRED)" if f.required else "(optional)"
            lines.append(f'  - "{f.name}": {type_label} {req}')

        if example:
            if schema.expect_array:
                example_json = json.dumps([example], indent=2)
            else:
                example_json = json.dumps(example, indent=2)
            lines.append(f"\nExample:\n```json\n{example_json}\n```")

        lines.append("\nIMPORTANT: Return ONLY valid JSON. No text before or after the JSON.")

        return "\n".join(lines)

    @staticmethod
    def get_xml_prompt_instruction(
        schema: ResponseSchema,
        example: Optional[dict] = None,
    ) -> str:
        """Generate a prompt instruction telling the AI to return XML-tagged output.

        Produces:
            <items>
              <faction>
                <name>string (REQUIRED)</name>
                <description>string</description>
                <goals>
                  <goal>string</goal>
                  <goal>string</goal>
                </goals>
              </faction>
            </items>
        """
        tag = schema.item_tag
        root = schema.root_tag

        lines = []
        if schema.expect_array:
            lines.append(
                f"Return your answer as XML with {schema.min_items} <{tag}> elements "
                f"inside a <{root}> wrapper."
            )
        else:
            lines.append(f"Return your answer as a single <{tag}> XML element.")

        lines.append("Use these child tags for each field:")

        for f in schema.fields:
            req = "(REQUIRED)" if f.required else "(optional)"
            if f.type == "list":
                # Show list fields with repeated child elements
                singular = f.name.rstrip('s') if f.name.endswith('s') else f.name
                lines.append(f"  <{f.name}> — contains multiple <{singular}> elements {req}")
            else:
                lines.append(f"  <{f.name}> — {f.type} {req}")

        # Build example
        if example:
            example_xml = _dict_to_xml(example, tag, schema)
            if schema.expect_array:
                example_xml = f"<{root}>\n{_indent(example_xml, 2)}\n</{root}>"
            lines.append(f"\nExample:\n```xml\n{example_xml}\n```")

        lines.append(f"\nIMPORTANT: Return ONLY valid XML. No text before or after the <{root if schema.expect_array else tag}> tags.")

        return "\n".join(lines)

    @staticmethod
    def get_xml_json_prompt_instruction(
        schema: ResponseSchema,
        example: Optional[dict] = None,
    ) -> str:
        """Generate a prompt instruction for XML-wrapped JSON hybrid format.

        Produces:
            <items>
              <faction>
              {"name": "...", "description": "...", "goals": [...]}
              </faction>
            </items>

        The XML tags act as clear delimiters while the content stays as
        type-rich JSON.  This can be easier for some models than pure XML.
        """
        tag = schema.item_tag
        root = schema.root_tag

        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array of strings",
            "dict": "object",
        }

        lines = []
        if schema.expect_array:
            lines.append(
                f"Return {schema.min_items} items. Wrap each item in <{tag}>...</{tag}> "
                f"XML tags, with a JSON object inside each tag."
            )
            lines.append(f"Wrap all items in <{root}>...</{root}>.")
        else:
            lines.append(
                f"Return a single <{tag}> XML tag containing a JSON object inside."
            )

        lines.append("\nThe JSON object inside each tag must have these fields:")
        for f in schema.fields:
            type_label = type_map.get(f.type, f.type)
            req = "(REQUIRED)" if f.required else "(optional)"
            lines.append(f'  - "{f.name}": {type_label} {req}')

        if example:
            example_json = json.dumps(example, indent=2)
            inner = f"<{tag}>\n{example_json}\n</{tag}>"
            if schema.expect_array:
                inner = f"<{root}>\n{_indent(inner, 2)}\n</{root}>"
            lines.append(f"\nExample:\n```xml\n{inner}\n```")

        lines.append(
            f"\nIMPORTANT: Each <{tag}> must contain ONLY a valid JSON object. "
            "No text outside the JSON inside each tag."
        )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level helpers (for XML generation)
# ---------------------------------------------------------------------------

def _dict_to_xml(d: dict, tag: str, schema: Optional[ResponseSchema] = None) -> str:
    """Convert a dict to a simple XML string for use in prompt examples.

    Not a full XML serializer — just enough for readable examples.
    """
    lines = [f"<{tag}>"]
    for key, value in d.items():
        if isinstance(value, list):
            singular = key.rstrip('s') if key.endswith('s') else key
            lines.append(f"  <{key}>")
            for item in value:
                lines.append(f"    <{singular}>{_xml_escape(str(item))}</{singular}>")
            lines.append(f"  </{key}>")
        elif isinstance(value, dict):
            # Nested dict: serialize as child tags
            inner = _dict_to_xml(value, key)
            lines.append(_indent(inner, 2))
        else:
            lines.append(f"  <{key}>{_xml_escape(str(value))}</{key}>")
    lines.append(f"</{tag}>")
    return "\n".join(lines)


def _xml_escape(text: str) -> str:
    """Escape special XML characters."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _indent(text: str, spaces: int) -> str:
    """Indent each line of text by the given number of spaces."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.split("\n"))
