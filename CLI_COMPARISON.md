# CLI Comparison: Current vs. New System

## Current CLI (v1)

```
═══════════════════════════════════════════════════════════════════════════════
                              INFINITE STORY ENGINE
═══════════════════════════════════════════════════════════════════════════════

                        THE VEIL OF THORNREACH

The cobblestone streets shimmer in the failing light. You can hear the distant 
sound of crowds gathering. Something is happening in the market.

═══════════════════════════════════════════════════════════════════════════════

Eira: I've heard whispers in the shadows. The curse is spreading faster now.

Thorne: Whatever we're going to do, we need to do it soon.

*The air grows cold as the sun dips below the horizon.*

═══════════════════════════════════════════════════════════════════════════════

What would you like to do?

1. Head toward the marketplace
2. Ask a nearby merchant what's going on
3. Find shelter and observe from afar
4. Write your own choice
5. Save and exit
6. Exit without saving

Your choice: 
```

### Current System Issues
- No visual structure (all segments look the same)
- No context about where you are in the story
- No indication of arc/episode progress
- No transparency about what's happening
- Can't see character state changes
- Can't see pacing pressure
- Just: text → choices → repeat

---

## New CLI - Gameplay Mode (Immersive)

```
═══════════════════════════════════════════════════════════════════════════════
                        THE VEIL OF THORNREACH
═══════════════════════════════════════════════════════════════════════════════

[EPISODE 2]

The cobblestone streets shimmer in the failing light. You can hear the distant 
sound of crowds gathering. Something is happening in the market.

─────────────────────────────────────────────────────────────────────────────

Eira: I've heard whispers in the shadows. The curse is spreading faster now.

Thorne: Whatever we're going to do, we need to do it soon.

*The air grows cold as the sun dips below the horizon.*

─────────────────────────────────────────────────────────────────────────────

What would you like to do?

1. Head toward the marketplace
2. Ask a nearby merchant what's going on
3. Find shelter and observe from afar
4. Write your own choice
5. Save and exit
6. Exit without saving

Your choice: 
```

### What's Different (Subtle)
- Optional episode banner when episode transitions
- Can be toggled off (SHOW_EPISODE_TRANSITIONS=false)
- Same immersive experience
- But structural awareness underneath

---

## New CLI - Exploration Mode (Debug)

```
═══════════════════════════════════════════════════════════════════════════════
                           EXPLORATION MODE
═══════════════════════════════════════════════════════════════════════════════

[WORLD] veil_of_thornreach        [ARC] 1: The Rebellion
[EPISODE] 2                        [TONE] betrayal, arc_heavy
[PROTAGONIST] Eira                 [PACING] 0.65               [PROXIMITY] 0.7

───────────────────────────────────────────────────────────────────────────────
SEGMENT seg_abc123 [ep:2, seg:14/~20, parent: seg_xyz789, status: generated]
───────────────────────────────────────────────────────────────────────────────

NARRATIVE:
  The cobblestone streets shimmer in the failing light. You can hear the 
  distant sound of crowds gathering. Something is happening in the market.
  
  Eira: I've heard whispers in the shadows. The curse is spreading faster now.
  
  Thorne: Whatever we're going to do, we need to do it soon.
  
  *The air grows cold as the sun dips below the horizon.*

CHARACTER STATES (snapshot from episode start):
  eira:   status=alive, mood=disillusioned, loyalty=rebel-aligned, location=market
  thorne: status=alive, mood=angry, loyalty=rebel-leader, location=market

CHANGE NOTES (accumulated this episode):
  seg_3:  eira learned about rebel plans
  seg_7:  thorne grew suspicious of council
  seg_14: eira confronted thorne about his motives

EPISODE INFO:
  Tone: betrayal, arc_heavy
  End condition: protagonist commits to a faction
  Progress: 70% done
  Protagonist alive: true

───────────────────────────────────────────────────────────────────────────────
CHOICES:
───────────────────────────────────────────────────────────────────────────────

1. Head toward the marketplace
   → to_segment: null [UNEXPLORED - will generate with current context]

2. Ask a nearby merchant what's going on
   → to_segment: seg_def456 [GENERATED - shared by all users who picked this]

3. Find shelter and observe from afar
   → to_segment: null [UNEXPLORED - will generate]

4. Write your own choice
   → to_segment: null [UNEXPLORED - custom choice will generate]

DEV COMMANDS:

5. [DEV] Show segment chain
   └─ Walk parent chain back to episode start

6. [DEV] Show episode recaps
   └─ Display summaries of completed episodes in this arc

7. [DEV] Show arc branches
   └─ See which other paths users have taken in this arc

8. [DEV] Toggle protagonist death
   └─ Manually test death handling

9. [GAMEPLAY] Switch to Gameplay Mode
   └─ Hide all context, show just story + choices

10. Save and exit

11. Exit without saving

Your choice: 
```

### What's Different (Complete Context)
- Every piece of information visible
- Arc, episode, tone, pacing weight
- Character states and changes
- Choice status (generated vs. unexplored)
- Dev commands for testing
- Can easily switch back to gameplay mode

---

## Mode Comparison Table

| Feature | Gameplay Mode | Exploration Mode |
|---------|---------------|------------------|
| **Text blocks** | ✅ Full content | ✅ Full content |
| **Choices** | ✅ Numbered list | ✅ With status info |
| **Episode info** | ⚠️ Subtle banner | ✅ Explicit section |
| **Arc info** | ❌ Hidden | ✅ In header |
| **Character states** | ❌ Hidden | ✅ Full display |
| **Change notes** | ❌ Hidden | ✅ Listed |
| **Pacing weight** | ❌ Hidden | ✅ Shown |
| **Proximity** | ❌ Hidden | ✅ Shown |
| **Segment ID** | ❌ Hidden | ✅ Shown |
| **Choice status** | ❌ Hidden | ✅ Shows generated vs unexplored |
| **Dev commands** | ❌ None | ✅ Multiple |
| **Visual clutter** | ✅ Minimal | ⚠️ Dense |
| **Immersive** | ✅ Very | ❌ Not at all |
| **Transparent** | ❌ Not at all | ✅ Fully |

---

## Usage Patterns

### Gameplay Mode Use Cases

**For actual storytelling:**
```
./run.sh veil_of_thornreach
# Open story in gameplay mode (default)
# Read immersively
# Make choices based on story, not mechanics
```

**Smooth transitions:**
```
Episode ends → Recap happens behind scenes → New episode begins
No visible loading, no interruption
Story just... continues with subtle tone shift
```

---

### Exploration Mode Use Cases

**For debugging:**
```
CLI_MODE=exploration ./run.sh veil_of_thornreach
# See full context
# Understand what the AI is being told
# Check character states accumulating
# Verify pacing progression
```

**For testing:**
```
In exploration mode:
1. Generate segments
2. Check character states updated
3. Watch pacing weight increase
4. Trigger episode end
5. See recap generation
6. Watch new episode tone
```

**For analysis:**
```
User asks: "Why did Eira suddenly change personality?"
Developer:
1. Switch to exploration mode
2. Navigate to that segment
3. See character state snapshot
4. See change notes
5. Check recap that happened
6. Understand the change
```

---

## Configuration

### Environment Variables

```bash
# Show gameplay or exploration mode
CLI_MODE=gameplay  # or "exploration"

# Only affect gameplay mode
SHOW_EPISODE_TRANSITIONS=true  # Show "[EPISODE 2]" banner?

# Only affect exploration mode
SHOW_PACING=true       # Show pacing_weight?
SHOW_CHARACTER_STATES=true  # Show character snapshots?
SHOW_SEGMENT_ID=true   # Show segment IDs?

# General
VERBOSE_LOGS=false     # Extra logging?
```

### Command-Line Overrides

```bash
# Start in exploration mode even if default is gameplay
./run.sh veil_of_thornreach --mode=exploration

# Change other settings via CLI
./run.sh veil_of_thornreach --show-episode-transitions=false
```

---

## Example Session: Gameplay Mode

```
$ ./run.sh veil_of_thornreach

[INFO] Creating virtual environment...
[INFO] Activating virtual environment...
[INFO] Installing requirements...
[INFO] Loading story 'veil_of_thornreach'...
[INFO] Starting the story CLI...

═══════════════════════════════════════════════════════════════════════════════
                        THE VEIL OF THORNREACH
═══════════════════════════════════════════════════════════════════════════════

You arrive in Thornreach at dusk. The city smells of incense and fear.

What would you like to do?

1. Find shelter for the night
2. Wander the streets and listen to rumors
3. Head to the tavern

Your choice: 2

[Generating next scene...]

═══════════════════════════════════════════════════════════════════════════════

As you walk through the winding streets, you overhear two merchants arguing.

"The curse is spreading," one hisses. "We need to do something before—"

"Before what?" the other interrupts. "Before the city burns?"

You duck into an alcove as they hurry past.

What would you like to do?

1. Follow the merchants
2. Return to the main street
3. Break into a nearby shop and look for supplies

Your choice: 
```

---

## Example Session: Exploration Mode

```
$ CLI_MODE=exploration ./run.sh veil_of_thornreach

[INFO] Starting in EXPLORATION MODE
[INFO] Loading story 'veil_of_thornreach'...

═════════════════════════════════════════════════════════════════════════════════════
                               EXPLORATION MODE
═════════════════════════════════════════════════════════════════════════════════════

[WORLD] veil_of_thornreach        [ARC] 1: The Rebellion
[EPISODE] 1                        [TONE] mystery, tension
[PROTAGONIST] eira                 [PACING] 0.15               [PROXIMITY] null

───────────────────────────────────────────────────────────────────────────────────────
SEGMENT seg_start_1 [ep:1, seg:1/~20, parent: none, status: generated]
───────────────────────────────────────────────────────────────────────────────────────

NARRATIVE:
  You arrive in Thornreach at dusk. The city smells of incense and fear.

CHARACTER STATES (snapshot from episode start):
  eira:    status=alive, mood=cautious, loyalty=neutral, location=city_entrance
  thorne:  status=unknown, mood=unknown, loyalty=unknown, location=unknown
  vendor:  status=alive, mood=fearful, loyalty=unclear, location=marketplace

CHANGE NOTES (accumulated this episode):
  (none yet - first segment)

EPISODE INFO:
  Tone: mystery, tension
  End condition: protagonist learns about the curse
  Progress: 5% done
  Protagonist alive: true

───────────────────────────────────────────────────────────────────────────────────────
CHOICES:
───────────────────────────────────────────────────────────────────────────────────────

1. Find shelter for the night
   → to_segment: null [UNEXPLORED - will generate]

2. Wander the streets and listen to rumors
   → to_segment: null [UNEXPLORED - will generate]

3. Head to the tavern
   → to_segment: null [UNEXPLORED - will generate]

DEV COMMANDS:

4. [DEV] Show segment chain
5. [DEV] Show episode recaps
6. [DEV] Show arc branches
7. [DEV] Toggle protagonist death
8. [GAMEPLAY] Switch to Gameplay Mode
9. Save and exit
10. Exit without saving

Your choice: 2

[Generating next scene...]

═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
[WORLD] veil_of_thornreach        [ARC] 1: The Rebellion
[EPISODE] 1                        [TONE] mystery, tension
[PROTAGONIST] eira                 [PACING] 0.25               [PROXIMITY] 0.1

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
SEGMENT seg_abc123 [ep:1, seg:2/~20, parent: seg_start_1, status: generated]
───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

NARRATIVE:
  As you walk through the winding streets, you overhear two merchants arguing.
  
  "The curse is spreading," one hisses. "We need to do something before—"
  
  "Before what?" the other interrupts. "Before the city burns?"
  
  You duck into an alcove as they hurry past.

CHARACTER STATES (snapshot from episode start):
  eira:    status=alive, mood=cautious, loyalty=neutral, location=marketplace
  thorne:  status=unknown, mood=unknown, loyalty=unknown, location=unknown
  vendor:  status=alive, mood=fearful, loyalty=unclear, location=marketplace

CHANGE NOTES (accumulated this episode):
  seg_2:  eira overheard about the curse spreading

EPISODE INFO:
  Tone: mystery, tension
  End condition: protagonist learns about the curse
  Progress: 10% done (getting closer to end condition!)
  Proximity: 0.1 (very far from ending)
  Protagonist alive: true

CHOICES:
  1. Follow the merchants → null [UNEXPLORED]
  2. Return to the main street → null [UNEXPLORED]
  3. Break into a nearby shop → null [UNEXPLORED]

DEV COMMANDS:

4. [DEV] Show segment chain
5. [DEV] Show episode recaps
6. [DEV] Show arc branches
7. [DEV] Toggle protagonist death
8. [GAMEPLAY] Switch to Gameplay Mode
9. Save and exit
10. Exit without saving

Your choice: 
```

---

## Key Differences Highlighted

| Aspect | v1 (Current) | v2 Gameplay | v2 Exploration |
|--------|-------------|-------------|-----------------|
| **Feels like** | Reading text | Reading novel | Playing game |
| **Structure awareness** | None | Implicit | Explicit |
| **State transparency** | Hidden | Hidden | Complete |
| **Dev-friendly** | No | No | Very |
| **Immersive** | Medium | High | Low |
| **Can debug** | No | Difficult | Easy |
| **Can understand system** | No | Inferrable | Yes |

---

## Switching Between Modes

```
In Exploration Mode:

Your choice: 8

[Switching to Gameplay Mode]

═══════════════════════════════════════════════════════════════════════════════
                        THE VEIL OF THORNREACH
═══════════════════════════════════════════════════════════════════════════════

As you walk through the winding streets, you overhear two merchants arguing.

"The curse is spreading," one hisses. "We need to do something before—"

"Before what?" the other interrupts. "Before the city burns?"

You duck into an alcove as they hurry past.

What would you like to do?

1. Follow the merchants
2. Return to the main street
3. Break into a nearby shop

Your choice: 
```

---

## Configuration Examples

### Developer Setup
```bash
# .env file
CLI_MODE=exploration
SHOW_EPISODE_TRANSITIONS=true
SHOW_PACING=true
SHOW_CHARACTER_STATES=true
SHOW_SEGMENT_ID=true
VERBOSE_LOGS=true
```

### Player Setup
```bash
# .env file
CLI_MODE=gameplay
SHOW_EPISODE_TRANSITIONS=false  # Seamless experience
VERBOSE_LOGS=false
```

### Hybrid Setup
```bash
# .env file
CLI_MODE=gameplay
SHOW_EPISODE_TRANSITIONS=true   # Know when things shift
VERBOSE_LOGS=false
```

---

## Summary

**Gameplay Mode** = Immersive storytelling
**Exploration Mode** = Transparent debugging + learning

Users can switch between them at any time, maintaining their progress.

Both modes read from the same shared segment graph.
Both modes display the same content.
The difference is just how much context is shown.

This allows:
- ✅ Players to enjoy immersive story
- ✅ Developers to debug easily
- ✅ Researchers to understand the system
- ✅ Testers to verify behavior
