# Prompt Building Structure Review

## Overview
The prompt building system is a multi-layered architecture that contextualizes story generation with narrative consistency, character state, and episode progression signals.

## Architecture Layers

### 1. **Segment Context Builder** (`backend/app/engine/segment_context_builder.py`)
**Purpose**: Build rich generation context by walking episode history and detecting transitions

**Core Methods**:
- `build_context(current_segment_id, user_choice)` - Main entry point
  - Walks backward through parent chain to episode start
  - Accumulates character state changes
  - Detects episode transitions
  - Calculates pacing weight
  - Returns context dict for AI generation

- `_walk_episode_chain(segment_id)` - Traverses parent chain
  - Stops at episode boundaries
  - Prevents circular references
  - Returns chronological segment list

- `_accumulate_changes(segment_chain)` - Collects story state
  - Aggregates all `change_notes` from chain
  - Provides context about what happened

- `_should_transition_episode(current_segment, changes)` - Episode transition logic
  - Triggers if `end_condition_proximity >= 0.8`
  - Triggers if `segment_number_in_episode >= 18`
  - Triggers if explicit end keywords found
  
- `_calculate_pacing_weight(segment, will_transition)` - Signals AI pacing
  - Quadratic curve: `(seg_num / 20)^2`
  - Values: 0.0 (start) → 0.99 (near end)
  - Signals "how much room is left" in episode

**Output Context**:
```python
{
    'previous_segments': [...],        # Last 5 scenes
    'character_states': {...},         # Latest snapshot
    'accumulated_changes': [...],      # All change_notes
    'episode_number': 1,               # Current episode
    'episode_tone': 'dark_and_mysterious',
    'episode_end_condition': 'character confronts villain',
    'segment_number_in_episode': 5,
    'should_transition_episode': False,
    'pacing_weight': 0.06,             # 5/20 segments
    'protagonist_id': 'char_1',
    'user_choice': 'Attack the guard',
}
```

---

### 2. **Scene Prompt Builder** (`backend/app/utils/prompt_builder.py`)
**Purpose**: Convert context into structured narrative prompt with intelligent entity filtering

**Core Methods**:
- `build_prompt(choice_text)` - Main prompt construction (109-209 lines)
  1. Extract relevant entities (chars/locations) based on:
     - Choice text mentions
     - Last 3 segments mentions
  2. Get story world context
  3. Fetch previous segments (max 5)
  4. Get current segment content
  5. Build multi-section prompt with priorities

- `_get_relevant_entity_ids(choice_text, lookback=3)` - Smart entity filtering
  - Scans choice text for character/location names
  - Looks back through N previous segments
  - Returns only relevant entities to reduce token usage
  - Prevents prompt bloat from listing all characters

- `_log_prompt_stats(prompt, prev_segments, chars, locs)` - Monitoring
  - Calculates approximate tokens (1 token ≈ 4 chars)
  - Logs prompt composition
  - Helps identify issues with size

**Prompt Structure** (Priority Order):
```
1. === CURRENT SCENE === (HIGHEST PRIORITY)
   - Scene description
   - Atmosphere
   - Characters present
   - Scene content

2. === PLAYER'S CHOICE ===
   - User's chosen action

3. === RECENT STORY ===
   - Last 5 segments summary

4. === WORLD CONTEXT ===
   - Story context (condensed)

5. === RELEVANT CHARACTERS (Available) ===
   - Max 5 characters not present

6. === RELEVANT LOCATIONS (Available) ===
   - Max 5 locations not present
```

**Key Features**:
- Token-aware: Limits sections to stay within limits
- Relevance-based: Only includes entities mentioned
- Hierarchical: Most important info first
- Extensible: Easy to add/reorder sections

---

### 3. **Character Context Builder** (`backend/app/utils/character_context_builder.py`)
**Purpose**: Enrich prompts with detailed character state and emotional arcs

**Core Methods**:
- `build_character_section(characters, current_segment_id, include_arcs, max_chars)` - Character info
  - Lists character name, description, avatar
  - Gets current state (emotion, status, notes)
  - Includes emotional arc summary if requested
  - Can limit to N most relevant characters

- `build_character_instructions(characters)` - AI consistency guidance
  - Lists character names
  - Warns about emotional consistency
  - Reminds about established details

- `extract_character_updates_from_text(generated_text, characters, segment_id)` - Parse changes
  - Looks for emotion keywords near character mentions
  - Extracts inferred character state from generated text
  - Simple heuristic: emotion word in 100-char window around name

- `integrate_character_context_into_prompt(prompt, characters, current_segment_id)` - Enhance
  - Appends character sections to existing prompt
  - Adds consistency instructions
  - Returns enhanced prompt

- `validate_and_apply_character_updates(characters, updates, max_emotional_change)` - Safety
  - Validates character updates
  - Applies to character objects
  - Warns if too many changes (>3) in one segment

**Character State Fields**:
```python
{
    "emotion": "afraid",      # happy, sad, angry, etc.
    "status": "present",      # present, absent, mentioned
    "notes": "was betrayed",  # Contextual notes
}
```

---

### 4. **Text Generator** (`backend/app/engine/generator.py`)
**Purpose**: Handle AI API calls with response validation and fallback

**Core Methods**:
- `generate(system_prompt, user_prompt, context_type)` - Main generation
  - Validates context_type (world, character, location, scene)
  - Combines system prompt with schema
  - Calls `_generate_content()` (implemented in subclasses)
  - Parses response JSON
  - Validates against response type schema
  - Returns parsed response or error

**Default System Prompt**:
```
- Expert storyteller role
- Maintain consistency
- Vivid descriptions
- Character consistency
- Advance story
- JSON response requirement
```

**Context Types**:
- `"world"` → WorldTextGeneratorResponse
- `"character"` → CharacterTextGeneratorResponse
- `"location"` → LocationTextGeneratorResponse
- `"scene"` → SceneTextGeneratorResponse

**Response Handling**:
- Extracts JSON from response using regex
- Validates against Pydantic schema
- Returns proper error if validation fails
- Logs all steps for debugging

---

## Integration Flow

```
User makes choice
    ↓
SegmentContextBuilder.build_context()
    ├─ Walk episode chain
    ├─ Accumulate changes
    ├─ Detect transitions
    └─ Calculate pacing → context dict
    ↓
ScenePromptBuilder.build_prompt()
    ├─ Extract relevant entities
    ├─ Get story context
    ├─ Fetch previous segments
    └─ Build hierarchical prompt
    ↓
(Optional) CharacterContextBuilder.integrate_character_context_into_prompt()
    ├─ Add character information
    └─ Add consistency instructions
    ↓
TextGenerator.generate()
    ├─ Prepare system + user prompts
    ├─ Call AI API (_generate_content)
    ├─ Parse JSON response
    ├─ Validate against schema
    └─ Return SceneTextGeneratorResponse
    ↓
StoryRunner._generate_segment()
    └─ Create segment with AI response
```

---

## Design Principles

### 1. **Separation of Concerns**
- **SegmentContextBuilder**: Episode/narrative logic
- **ScenePromptBuilder**: Token management & prioritization
- **CharacterContextBuilder**: Character state consistency
- **TextGenerator**: AI API abstraction

### 2. **Token Efficiency**
- Limits previous segments to 5
- Filters entities by relevance
- Caps character/location sections to 5 each
- Hierarchical structure: important info first

### 3. **Consistency Maintenance**
- Character state tracking
- Change notes accumulation
- Emotional arc awareness
- Episode tone/end condition context

### 4. **Extensibility**
- Easy to add new prompt sections
- Character context can be toggled
- Pacing calculation is customizable
- Response types are pluggable

### 5. **Robustness**
- Handles missing segments gracefully
- Prevents circular references
- Validates all JSON responses
- Comprehensive logging for debugging

---

## Configuration Points

### SegmentContextBuilder
- `lookback` in entity extraction (default: 3 segments)
- `max_segments` in pacing calculation (default: 20)
- End condition keywords list
- Segment count threshold (default: 18)

### ScenePromptBuilder
- `max_depth` for previous segments (default: 5)
- `max_chars` limit in relevant entities (default: 5)
- `max_locs` limit in relevant locations (default: 5)
- Prompt section order/priority

### CharacterContextBuilder
- `max_chars` limit (default: 10)
- `max_emotional_change` threshold (default: 3)
- Emotion keyword dictionary
- Context window size for emotion detection (default: 100 chars)

### TextGenerator
- `temperature` (default: 0.7)
- `max_tokens` (default: 1000)
- Default system prompt text

---

## Key Metrics & Signals

### Pacing Weight
- **Formula**: `(segment_number / 20)^2`
- **Values**: 0.0 (start) → 0.99 (end)
- **Purpose**: Signal to AI how much "room" is left
- **Examples**:
  - Segment 1: (1/20)² = 0.0025
  - Segment 10: (10/20)² = 0.25
  - Segment 18: (18/20)² = 0.81
  - Segment 20: capped at 0.99

### End Condition Proximity
- **Range**: 0.0 (far) → 1.0 (reached)
- **Triggers Transition**: >= 0.8
- **Set by**: AI generator in response

### Segment Count Limit
- **Hard Limit**: 18 segments per episode
- **Reason**: Keep episodes focused and paced
- **Fallback**: Transition if reached

---

## Token Budget Considerations

Typical prompt size:
- System prompt: ~150-200 tokens
- Context dict: ~50-100 tokens
- Previous segments: ~200-300 tokens
- Character info: ~100-200 tokens
- **Total**: ~500-800 tokens per request
- **Leaves**: ~200-500 tokens for response (at 1000 token limit)

For efficiency improvements:
- Reduce `max_depth` (segments to include)
- Reduce `max_chars`/`max_locs` limits
- Compress story context more
- Use character delta instead of full state

---

## Example: Complete Prompt Generation

```python
# 1. Build context
builder = SegmentContextBuilder(story)
context = builder.build_context("seg_5", "Attack the guard")
# Returns: pacing_weight=0.06, changes=[...], etc.

# 2. Build scene prompt
prompt_builder = ScenePromptBuilder(current_segment)
prompt = prompt_builder.build_prompt("Attack the guard")
# Returns: "=== CURRENT SCENE ===\n..."

# 3. Optionally enhance with character context
chars = [char_1, char_2]
prompt = CharacterContextBuilder.integrate_character_context_into_prompt(
    prompt, chars, "seg_5"
)

# 4. Generate with AI
generator = TextGenerator()
response = await generator.generate(
    system_prompt="",  # Uses default
    user_prompt=prompt,
    context_type="scene"
)
# Returns: SceneTextGeneratorResponse with all fields
```

---

## Potential Improvements

1. **Dynamic Token Allocation**: Adjust section sizes based on actual token usage
2. **Character Delta**: Send only state changes, not full state
3. **Segment Compression**: Summarize older segments more aggressively
4. **Emotion Arc Tracking**: Full emotional trajectory, not just current state
5. **Conditional Sections**: Skip sections if not relevant
6. **Caching**: Cache previous_segments if they don't change
7. **Streaming**: Stream AI responses for better UX
8. **A/B Testing**: Test different prompt structures

