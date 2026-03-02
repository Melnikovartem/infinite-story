# Vision: Shared Graph + Narrative Overlays

## Core Concept

**The Infinite Story Engine creates a living world that many users explore simultaneously, each experiencing a unique journey while collectively building a shared narrative.**

Instead of everyone reading the same story or everyone getting a randomly generated story, we've designed a hybrid system:

- **The World is Shared** — locations, characters, lore, rules exist once
- **The Journeys are Unique** — each user's path through the world is personal
- **The Narrative is Structured** — episodes and arcs give shape to the chaos
- **The Graph is Immutable** — once a segment is generated, it's permanent and shared

### Mental Model: A Living World

Think of it like this:

```
You are a god observing a world. The world has its own timeline of events:
- A rebellion is stirring
- A curse is spreading
- Characters are making their own choices

You can influence the story by making choices, but you're not the only observer.
Other gods are watching too, from different angles, making different choices.

Sometimes your paths cross (you visit the same location, meet the same NPC).
After a while, the world's timeline stabilizes (compression) and continues forward.

The world feels alive because it's not built just for you — it's a place where
multiple perspectives create a complex, shifting narrative.
```

---

## Key Design Decisions

### 1. Segments Are Shared, Not Per-User

**What this means:**

When a segment is generated, it's generated **once** and **shared** by all users who reach it via the same choice.

```
Segment A: "You arrive in the marketplace"
  ├── Choice 1: "Head to the tavern" → Segment B (SHARED)
  ├── Choice 2: "Visit the merchant" → Segment C (SHARED)
  └── Choice 3: "Find an informant" → [unexplored]
```

If User X picks "Head to the tavern", Segment B is generated. If User Y later picks the same choice, they get the **exact same Segment B**. No duplication, no inconsistency.

**Why:**
- Prevents narrative fragmentation
- Guarantees consistency for shared locations/characters
- Reduces storage and computation
- Creates a real world with real paths through it

**Tradeoff:**
- If Segment B was generated under User X's episode context, User Y might read it in a different episode context
- Solution: We accept this. The world is what it is. Not everything aligns perfectly with your personal arc, and that's okay.

---

### 2. Episodes Are Narrative Overlays, Not Containers

**What this means:**

Episodes don't "contain" segments. Instead, episodes are **narrative context** that gets **baked into segments at generation time**.

```
Segment 1 [arc:1, ep:1, tone:mystery] → Segment 2 [arc:1, ep:1, tone:mystery]
  → Segment 19 [arc:1, ep:1, end_proximity:0.9]
    → Segment 20a [arc:1, ep:2, tone:betrayal]     (choice A → new episode)
    → Segment 20b [arc:1, ep:2, tone:action]       (choice B → different episode)
    → Segment 20c [arc:1, ep:1, tone:mystery]      (choice C → same episode)
```

Notice: Different branches from the same segment can start different episodes. Episodes don't follow users — they're baked into the graph structure.

**Why:**
- Episodes aren't "for the player" — they're structural markers in the world's narrative
- Multiple users can be in different episodes while traversing the same segment graph
- Episode transitions are seamless (no loading screens, just tonal shifts)
- Allows branching episode variants (4a, 4b, 4c)

---

### 3. Character State = Snapshot + Running Log

**What this means:**

At the start of each episode, characters have a **snapshot state**. As segments are generated, **change notes accumulate**. At episode end, a **recap reconciles** everything into a new snapshot.

```
Episode 1 Start:
  character_states: { eira: { status: alive, mood: hopeful } }

Segment 1: change_notes: [{ eira: "learned about the curse" }]
Segment 7: change_notes: [{ eira: "betrayed by council member" }]
Segment 19: change_notes: [{ eira: "fled the city" }]

Episode 1 Recap:
  character_states_final: { eira: { status: alive, mood: determined, location: outskirts } }
  
Episode 2 starts with new snapshot from recap.
```

**Why:**
- Prevents character state from becoming inconsistent
- Allows the recap generation to be context-aware (AI reads all changes, outputs coherent state)
- Snapshot at episode start makes context building efficient
- Change notes are lightweight (just text descriptions)

---

### 4. Arc Compression = Mainline Selection

**What this means:**

After 10-15 episodes, the system becomes "too wide" — too many branches. The world picks a **canonical path** and archives the rest.

```
Arc 1: The Rebellion (15 episodes, many branches)
  seg_1 → seg_2 → seg_5 → seg_12 → ... → seg_87
                     ↗     ↘
                 seg_4    seg_6 (archived)
                 seg_3    seg_7 (archived)

Compression:
  AI reviews all branches
  Picks mainline: seg_1 → seg_2 → seg_5 → seg_12 → ... → seg_87
  Archives: everything else
  
Arc 2: The Siege (starts from seg_87)
```

**Why:**
- Prevents combinatorial explosion
- Gives narrative shape: world has a "canon" path, even though multiple paths were explored
- Feels like the world is settling on what "really happened"
- Allows new arcs to start from a stable state

**Player experience:**
- Your personal branch might have been archived
- But the story continues for everyone from the mainline
- Intentionally feels like "the gods are choosing reality"

---

### 5. User Sessions Are Just Cursors

**What this means:**

A user session doesn't carry state. It's literally just:

```python
user_session = {
    current_segment_id: "seg_abc123",
    visited_segments: ["seg_1", "seg_2", "seg_5", ...]
}
```

No per-user episode tracking. No per-user character states. No per-user protagonist tracking. The user is a cursor moving through the shared graph.

**Why:**
- Simple, scalable
- No per-user state duplication
- All state lives on segments
- Easy to understand and debug

**What about personalization?**
- Comes from the path you take (different choices, different segments visited)
- Comes from episode context when you enter a segment (might feel different depending on what was happening in the world when you arrived)
- Comes from character relationships and knowledge accumulation

---

## Architecture Overview

### The Segment Graph

```
        Segment (immutable node)
        ├── text_blocks (the content users read)
        ├── outgoing_choices (pointers to next segments)
        ├── status (generated, archived, etc.)
        └── episode_context (arc, episode, tone, pacing, character_states)

        Choice (immutable edge)
        ├── from_segment_id
        ├── to_segment_id (null = unexplored, points to segment if explored)
        └── click_count
```

### The Episode Layer

```
        EpisodeRecap (generated at episode end)
        ├── title, summary
        ├── character_states_final (snapshot for next episode)
        ├── world_state_changes
        └── narrative_threads (seeds for next episode)
        
        When new episode starts:
        ├── Random tone word
        ├── Arc storyline
        ├── Previous recap
        └── AI generates: tone_tags, end_condition, narrative direction
```

### The Arc Layer

```
        StoryArc (meta-container)
        ├── arc_number (1, 2, 3, ...)
        ├── key_events
        ├── episode_recaps (generated during play)
        └── compression_result (mainline + archived)
        
        Compression flow:
        ├── Identify all branches
        ├── Select top popular + random candidates
        ├── AI picks mainline
        ├── Archive non-mainline segments
        └── Continue to next arc from mainline frontier
```

### The User Session Layer

```
        UserSession (minimal state)
        ├── current_segment_id
        └── visited_segments
        
        Everything else comes from segments.
        No duplication, no divergence.
```

---

## Generation Flow

### When User Picks an Unexplored Choice

```
1. CHECK: Is choice.to_segment_id null?
   └─ If null → segment doesn't exist yet, generate it
   
2. BUILD CONTEXT:
   ├─ Walk parent chain to find episode start
   ├─ Collect character snapshot from episode start
   ├─ Collect all change_notes accumulated so far
   ├─ Determine if episode should end (pacing pressure, end_condition proximity)
   ├─ If YES → generate recap + new episode context
   ├─ If NO → continue current episode context
   └─ Calculate pacing_weight for this segment
   
3. GENERATE SEGMENT:
   ├─ Build prompt with: world, arc, episode, character states, recent segments
   ├─ AI generates: text_blocks, choices, change_notes, end_condition_proximity
   ├─ Create new Segment with all context baked in
   ├─ Save to disk (immutable)
   └─ Update choice.to_segment_id
   
4. MOVE CURSOR:
   └─ UserSession.current_segment_id = new segment
   
5. SAVE STATE:
   └─ Persist user session
```

### When Episode Ends

```
1. DETECT: Previous segment has end_condition_proximity ≈ 1.0
   
2. GENERATE RECAP:
   ├─ Walk back to episode start
   ├─ Collect all segments + all change_notes
   ├─ Call AI: "Given these changes, what's the final character state?"
   ├─ AI outputs: episode title, summary, character_states_final, threads
   ├─ Save EpisodeRecap to disk
   
3. GENERATE NEW EPISODE:
   ├─ Pick random tone word
   ├─ Get arc storyline + previous recaps
   ├─ Call AI: "Generate new episode with tone X, given recap Y"
   ├─ AI outputs: tone_tags, end_condition, narrative hooks
   
4. NEXT SEGMENT STARTS NEW EPISODE:
   └─ All outgoing choices from trigger segment start with new episode context
```

### When Arc Ends (~15 episodes)

```
1. DETECT: Reached 15 episodes in arc
   
2. FIND BRANCHES:
   ├─ Query all user sessions
   ├─ Identify paths taken through segment graph
   ├─ Get top N by traversals, M random
   
3. SUMMARIZE:
   ├─ For each candidate branch, generate summary
   ├─ Include: key events, character arcs, outcomes
   
4. AI PICKS MAINLINE:
   ├─ Call AI: "Which branch is the best continuation?"
   ├─ AI considers: narrative coherence, character arcs, world consistency
   
5. ARCHIVE:
   ├─ Mark all non-mainline segments as "archived"
   ├─ Hidden by default (can be recovered for research)
   
6. CONTINUE:
   ├─ Next arc starts from mainline frontier
   ├─ All users entering arc 2 start from same point
```

---

## User Experience

### Gameplay Mode (Default)

Immersive storytelling experience. Just the story and choices.

```
═══════════════════════════════════════════════════════════════
                    THE VEIL OF THORNREACH
═══════════════════════════════════════════════════════════════

The cobblestone streets shimmer in the failing light. You can 
hear the distant sound of crowds gathering. Something is 
happening in the market.

—————————————————————————————————————————————————————————————————

1. Head toward the marketplace
2. Ask a nearby merchant what's going on
3. Find shelter and observe from afar

Your choice:
```

**Features:**
- Clean, distraction-free
- Minimal metadata
- Subtle episode indicators (optional)
- Feels like reading a novel

---

### Exploration Mode (Optional)

Full context visibility for players who want to understand the system.

```
[WORLD] veil_of_thornreach  [ARC] 1: The Rebellion  [EP] 3  [TONE] betrayal
[PROTAGONIST] Eira  [PACING] 0.65  [PROXIMITY] 0.7

SEGMENT seg_abc123 [ep:3, seg:14/~20, status: generated]

NARRATIVE:
  The cobblestone streets shimmer...

CHARACTER STATES (episode start):
  eira:   alive, disillusioned, rebel-aligned
  thorne: alive, angry, rebel-leader

CHANGE NOTES (accumulated):
  seg_3:  eira learned about rebel plans
  seg_14: eira confronted thorne

CHOICES:
  1. Head toward the marketplace → null [UNEXPLORED]
  2. Ask merchant → seg_def456 [GENERATED - shared]
  3. Find shelter → null [UNEXPLORED]
```

**Features:**
- Full transparency
- See episode/arc/character context
- Understand pacing pressure
- Dev commands for testing
- Great for understanding system mechanics

---

## Important Principles

### 1. The World Is Real

Characters don't exist just for you. They have their own arcs, their own knowledge, their own relationships. If you don't talk to someone, they don't know about you.

### 2. Segments Are Permanent

Once generated, a segment doesn't change. If you take a path that someone else has taken, you read what they caused to be written. This isn't a bug — it's the point.

### 3. Branching Is Temporary

Your personal branch might be archived. Other people's choices matter too. This is uncomfortable intentionally — it's what it feels like to live in a world with agency beyond your own.

### 4. Episodes Provide Shape

Without episodes, stories are shapeless trees. Episodes give narrative rhythm. They're where the AI resets its context and picks a new tone. They're how chaos becomes story.

### 5. Arcs Provide Closure

Arc compression is the system saying: "Okay, this is what actually happened." It's jarring because it's meant to be — you're gods playing with timelines, and one becomes real.

---

## Comparison to Other Systems

### vs. Linear Story (Book/Movie)

| Dimension | Book | Infinite Story |
|-----------|------|-----------------|
| Structure | Fixed | Episodes/Arcs |
| Branching | None | Temporary (archived) |
| Uniqueness | None | Many paths |
| Narrative | Authored | AI-generated but guided |
| Character consistency | Guaranteed | Cumulative + snapshots |

### vs. Choose Your Own Adventure

| Dimension | CYOA | Infinite Story |
|-----------|------|-----------------|
| Choices | Curated | Open-ended |
| Content | Pre-written | AI-generated |
| Sharing | Per-branch | Per-segment |
| Branching | Permanent | Temporary (archive) |
| Scale | Limited | Unbounded (with compression) |

### vs. Procedural Generation

| Dimension | Procedural | Infinite Story |
|-----------|-----------|-----------------|
| Consistency | Low | High (segments immutable) |
| Sharing | Per-user | Shared |
| Narrative | Random | Guided by episodes |
| Branching | Unbounded | Bounded by compression |
| Character arcs | Weak | Strong (via snapshots) |

---

## Technical Highlights

### Immutability

Segments never change once generated. This gives:
- **Consistency**: Same segment always has same content
- **Shareability**: Safe for multiple users to traverse
- **Debuggability**: Can trace issues to generation context
- **Archivability**: Can preserve history, restore branches

### Narrative Overlays

Episodes and arcs are not structural — they're metadata. This gives:
- **Flexibility**: Branches can start different episodes
- **Simplicity**: Graph is just segments + choices
- **Efficiency**: No "episode container" data structure
- **Seamlessness**: Transitions happen at generation time

### Lightweight User State

Sessions are minimal (just cursor position). This gives:
- **Scalability**: Can handle many users
- **Simplicity**: No complex state synchronization
- **Clarity**: All behavior driven by segments, not user state
- **Shareability**: Users see same segments

---

## Known Limitations

### 1. First Generation Wins

When you pick an unexplored choice, that choice gets generated in **your** episode context. Whoever picks it next sees it in **their** episode context. This creates minor tonal mismatches.

**Mitigation:** We accept this. It's the cost of sharing. Episodes are narrative context, not rigid containers.

### 2. Compression Is Irreversible

Once an arc compresses, archived branches are hidden. They can be recovered but not played forward from.

**Mitigation:** Before compression, AI reviews multiple branches. Users should be aware compression will happen and enjoy their branch while it exists.

### 3. Character Knowledge Doesn't Spread

If Character A learns something about Character B, Character B doesn't automatically know it back. Knowledge is one-directional based on interactions.

**Mitigation:** This is actually realistic. Characters aren't omniscient. They learn through encounters.

### 4. Protagonist Death Switches Perspective

If your protagonist dies, the story continues from someone else's POV. You lose your original perspective.

**Mitigation:** This is intentional. Death matters. The world doesn't revolve around you.

---

## Future Enhancements

### Phase 2: Multi-Threaded Arcs

Instead of all users exploring one arc at a time, different arcs could run in parallel (one main, multiple side). Users could focus on their interest.

### Phase 3: Explicit Protagonist Selection

Instead of AI picking the next protagonist, offer users a choice: "Your character died. Who would you like to follow?"

### Phase 4: Community Curation

Let editors review archived branches and decide which deserve resurrection or which are canon before compression.

### Phase 5: Branching Quests

Minor branches that don't affect mainline but offer interesting side stories. Like side quests in games.

### Phase 6: Timeline Awareness

Let characters/NPCs be aware of compression and alternate timelines. "I remember when things went differently..."

---

## Summary

The Infinite Story Engine is a **world simulator** where:
- Many users explore **simultaneously**
- Segments are **immutable and shared**
- Episodes provide **narrative rhythm**
- Arcs provide **closure and mainlines**
- Characters **accumulate state** through recaps
- Compression **stabilizes the timeline**

It's not a book (too much branching), not a game (no gameplay mechanics), not random (guided by episodes). It's a new form: **collaborative temporal exploration through an evolving narrative world**.
