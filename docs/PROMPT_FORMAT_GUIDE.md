# Prompt Format Guide

The system uses a **lenient input format** for AI prompts and **JSON output** for responses.

## Design Philosophy

- **INPUT (to AI)**: Natural, readable format with sections and bullet points
  - Easy for AI to understand
  - Human-readable for debugging
  - No syntax requirements
  - Clear context and instructions

- **OUTPUT (from AI)**: Structured JSON
  - Validates required fields
  - Easy to parse and verify
  - Type-safe integration with backend
  - Clear contract between AI and system

## Scene Generation Example

### Input Prompt Format

```
=== STORY CONTEXT ===
The player chose: Approach the mysterious stranger in the tavern

Episode 1, Scene 5
Tone: Dark and mysterious
Episode goal: Uncover the conspiracy

=== RECENT STORY ===
• A hooded figure enters the tavern and orders a drink
• You notice they keep glancing at the door
• The tavern grows quiet as tension fills the air

=== EPISODES IN THIS ARC ===
• Episode 1: Dark and mysterious (5 scenes)

=== CHARACTER REFERENCE ===
• Barkeep (present)
• Hooded Figure (present)
• Merchant (absent)

=== PACING ===
Progress through episode: Mid-episode (25%)

=== GENERATION INSTRUCTIONS ===
Write the next scene that:
1. Follows naturally from the player's choice
2. Maintains the episode tone and goals
3. Respects character states and relationships
4. Advances the story forward
5. Provides meaningful next choices

Respond with JSON containing: short_description, text, atmosphere,
time_of_day, weather, characters_present, locations_present, choice_1, choice_2
```

### Output Format (JSON)

```json
{
  "short_description": "A tense conversation with a stranger",
  "text": "You approach the stranger with careful steps...",
  "atmosphere": "Tense and mysterious",
  "time_of_day": "Late evening",
  "weather": "Clear",
  "characters_present": ["barkeep", "hooded_figure"],
  "locations_present": ["tavern"],
  "choice_1": "Ask about their identity",
  "choice_2": "Offer to buy them a drink",
  "end_condition_proximity": 0.2,
  "error": null
}
```

## Prompt Format Examples

### World Generation Input

```
=== WORLD GENERATION REQUEST ===

Context: A medieval fantasy world with ancient magic

Key themes: Power, duty, mystery, tradition

Tone: Epic and dark

Create a detailed world with:
• Name and premise
• Overall themes and tone
• Key locations
• History and current state

Respond with JSON containing: name, premise, themes,
key_locations, history, current_state
```

### Character Generation Input

```
=== CHARACTER GENERATION REQUEST ===

Context: A noble trying to protect their family

Role in story: Mentor figure to the protagonist

Story tone: Dark and introspective

Create a compelling character with:
• Distinct name and appearance
• Clear personality and motivations
• Interesting background
• Relationships to other characters
• Current emotional state

Respond with JSON containing: name, description, personality,
motivation, background, current_status
```

### Choice Generation Input

```
=== CHOICE GENERATION REQUEST ===

Current scene: Standing at a crossroads in an ancient forest

Character situation: The protagonist is being pursued but unsure which path is safe

What's at stake: Their life and the fate of their companions

Generate 2-3 meaningful choices that:
• Are distinct from each other
• Fit the character's situation
• Lead to different story outcomes
• Feel natural and not forced

Respond with JSON containing: choice_1, choice_2, and optionally choice_3
```

## Key Benefits

### Input Format Benefits
✅ **Readable**: Easy for humans to debug and understand
✅ **Flexible**: No strict JSON syntax required
✅ **Natural**: Uses bullet points and sections like human writing
✅ **Context-Rich**: All relevant story info in one place
✅ **Error-Tolerant**: AI can focus on content, not formatting

### Output Format Benefits
✅ **Validated**: All required fields must be present
✅ **Parseable**: Direct mapping to backend objects
✅ **Typesafe**: Pydantic validation catches errors
✅ **Consistent**: Predictable structure for responses

## Integration Flow

```
Story Context
    ↓
SegmentContextBuilder.build_context()
    ├─ Walk parent chain
    ├─ Gather episodes/arcs
    ├─ Accumulate changes
    └─ Calculate signals
    ↓
PromptFormatter.format_scene_context()
    ├─ Structure as readable sections
    ├─ Add recent story recap
    ├─ Include character reference
    ├─ Show pacing progress
    └─ Provide clear instructions
    ↓
TextGenerator.generate()
    ├─ Send lenient input prompt
    ├─ Receive JSON response
    ├─ Validate with Pydantic
    └─ Return parsed object
    ↓
StoryRunner._generate_segment()
    └─ Create segment from response
```

## Section Types

### STORY CONTEXT
- What the player chose
- Current episode and scene number
- Episode tone and goals

### RECENT STORY
- Bullet-point summary of last 3 scenes
- Helps AI understand immediate context

### EPISODES IN ARC
- All episodes in current story arc
- Shows episode progression
- Provides thematic continuity

### CHARACTER REFERENCE
- Quick character name list
- Current status or role
- Helps AI maintain consistency

### PACING
- Human-readable progress indicator
- "Just starting", "Mid-episode", "Near the end"
- Guides AI's narrative pacing

### GENERATION INSTRUCTIONS
- What the AI needs to create
- Quality requirements
- Output format specification

## Customization

Prompts can be customized per story arc by adjusting:
- Section order (most important first)
- Detail level (more verbose for complex scenes)
- Character list (filtered by relevance)
- Pacing descriptions (custom labels)

## Backward Compatibility

The lenient input format is independent of output validation.
- Input: Natural, flexible format
- Output: Strict JSON with validation
- AI isn't forced to match rigid input structure

This separation allows flexibility in what AI reads while maintaining
integrity in what gets stored.

