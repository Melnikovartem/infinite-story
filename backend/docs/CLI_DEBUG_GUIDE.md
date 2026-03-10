# CLI Debug Guide

The unified story interface provides powerful debugging capabilities for AI-powered narrative generation.

## Interactive Mode

Default mode - play a story with full debugging access.

```bash
./run.sh my_story
```

Shows:
- Current segment with formatted text blocks
- Interactive menu with debugging options

Menu options while playing:
- **`1-N`** - Pick a choice and advance the story
- **`L`** - Toggle debug logging (ERROR ↔ DEBUG)
- **`I`** - View segment info panel (metadata, pacing, arc, characters, factions, magic, context summary)
- **`P`** - View formatted AI prompt (with token count)

## Non-Interactive Modes

### Auto-pick through scenes

Auto-select the first choice N times to navigate through story quickly.

```bash
# Navigate through 5 scenes automatically
./run.sh my_story --auto-pick 5

# Auto-pick indefinitely (0 = unlimited)
./run.sh my_story --auto-pick 0

# Auto-pick 5, then switch to interactive
./run.sh my_story --auto-pick 5
```

### Debug Info Dump

Auto-pick through scenes, then dump debug info and exit (no interaction).

#### Segment Info
Metadata, pacing bars, arc details, character emotions, running changes, etc.

```bash
# Opening scene info
./run.sh my_story --dump info

# Scene 2 info
./run.sh my_story --auto-pick 1 --dump info

# Scene 5 info
./run.sh my_story --auto-pick 4 --dump info
```

#### AI Prompt
Full formatted prompt sent to the AI (system + user + instructions).

```bash
# Opening prompt
./run.sh my_story --dump prompt

# Scene 3 prompt
./run.sh my_story --auto-pick 2 --dump prompt
```

#### Both Info + Prompt
Print both segment info and AI prompt.

```bash
./run.sh my_story --auto-pick 1 --dump all
```

### Context Dict Export

Export full generation context as JSON (for external analysis, testing, etc).

```bash
# Opening scene context
./run.sh my_story --dump-context

# Scene 2 context
./run.sh my_story --auto-pick 1 --dump-context > context.json

# Parse specific fields
./run.sh my_story --auto-pick 1 --dump-context | jq '.arc_characters | keys'
```

Context includes:
- World context (fundamental truths, worldbuilding)
- Previous arcs (recaps, outcomes, unresolved threads)
- Current arc (premise, conflict, themes, mysteries, hooks)
- Episodes (in-arc episode summaries)
- Episode recaps (bridging context)
- Characters (by hierarchy: protagonist > major > minor)
- Factions (with goals and allegiances)
- Magic/tech systems (with rules and costs)
- Locations
- Story dynamics (tension, momentum, pacing)
- Recent segments (full text for narrative continuity)
- Running changes (entity state deltas)

## Debug Logging

Enable debug-level logging to see raw AI requests/responses and detailed generation flow.

```bash
# Interactive mode with debug logs
./run.sh my_story --log-level debug

# Non-interactive with debug logs
./run.sh my_story --auto-pick 1 --dump info --log-level debug
```

Debug logs include:
- Full system prompt
- Full user prompt (with all context)
- Raw AI response (before parsing)
- Generation timing and flow events

Logs go to `~/.infinite_story_logs/` or output stream depending on configuration.

## Combined Examples

### Test scene generation with full context visibility

```bash
# See prompt + info + logs for scene 3
./run.sh my_story --auto-pick 2 --dump all --log-level debug

# Export context for scene 5
./run.sh my_story --auto-pick 4 --dump-context | jq '.' | less

# Check character states through generation
./run.sh my_story --auto-pick 1 --dump-context | jq '.arc_characters | to_entries[] | {name: .value.name, status: .value.status}'
```

### Integration testing

```bash
# Generate JSON for external AI testing
./run.sh my_story --auto-pick 3 --dump-context > test_context.json

# Run through 10 scenes without interaction
./run.sh my_story --auto-pick 10
```

## Tips

- **Testing story logic**: Use `--dump info` to verify metadata (pacing, episode transitions, etc)
- **Debugging AI output**: Use `--dump prompt` + `--log-level debug` to see exactly what was sent to the LLM
- **Analyzing generation**: Export context with `--dump-context` and use jq to inspect specific fields
- **Quick navigation**: `--auto-pick 0` skips all user input and runs indefinitely (stops on no choices)
- **Resume sessions**: Add `--resume` to any command to continue from last save
