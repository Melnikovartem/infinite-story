# CLEANUP INVENTORY: Phase 1-3 Detailed Breakdown

**Date Created:** March 3, 2026  
**Purpose:** Complete reference guide for code cleanup tasks  
**Status:** Ready for execution

---

## PHASE 1: DELETE IMMEDIATELY (No Dependencies)

### Total Impact: 1,533 lines, ~54 KB freed, 0 broken imports

---

## PHASE 1 ITEM #1: arc_compressor.py

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/engine/arc_compressor.py`
- **Line Range:** 1-301 (entire file)
- **Type:** Class Definition
- **Size:** 301 lines, ~11 KB
- **Complexity:** Medium - async operations, AI integration

### Components to Delete
```python
Lines 1-11:    Module docstring and imports
Lines 13-301:  Class ArcCompressor with 7 methods:
  - __init__(self, story: Story, generator: TextGenerator)              [lines 16-25]
  - async compress_arc(self, arc_id: str)                             [lines 27-105]
  - _find_branches_in_arc(self, arc_id: str)                          [lines 107-145]
  - _walk_forward_from(self, segment_id: str)                         [lines 147-174]
  - _select_candidates(self, branches: List[List[str]])               [lines 176-209]
  - async _summarize_branch(self, branch: List[str])                  [lines 211-237]
  - async _ai_select_mainline(self, arc: StoryArc, branch_summaries)  [lines 239-301]
```

### Dependencies
**Imports Used:**
```python
from typing import List, Dict, Set, Optional
import logging
import random
from app.models import Story, StorySegment, StoryArc, ArcCompressionResult
from app.models.story_segment import SegmentStatus
from app.engine.generator import TextGenerator
```

**Nothing imports this file** ✓

### Verification
- ✅ No imports found in any production files
- ✅ Not referenced in `app/engine/__init__.py`
- ✅ No test files depend on it (no test_arc_compressor.py usage)
- ✅ Safe to delete

### Deletion Checklist
- [ ] Verify no imports exist (run grep)
- [ ] Delete entire file
- [ ] Run test suite to confirm no breakage

---

## PHASE 1 ITEM #2: lenient_parser.py

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/engine/lenient_parser.py`
- **Line Range:** 1-506 (entire file)
- **Type:** Utility Class with Static Methods
- **Size:** 506 lines, ~18 KB
- **Complexity:** Low - pure functions with no state

### Components to Delete
```python
Lines 1-17:    Module docstring and imports
Lines 19-506:  Class LenientParser with 11 static methods:
  - parse_key_value(text: str)                                        [lines 22-61]
  - parse_list(text: str, separator: str = ',')                       [lines 63-78]
  - extract_section(text: str, section_name: str)                     [lines 80-103]
  - clean_text(text: str)                                             [lines 105-130]
  - extract_json_like(text: str)                                      [lines 132-156]
  - merge_dicts(base, parsed, key_mapping)                            [lines 158-187]
  - parse_scene_response(text: str)                                   [lines 189-273]
  - parse_world_response(text: str)                                   [lines 275-335]
  - parse_character_response(text: str)                               [lines 337-395]
  - parse_location_response(text: str)                                [lines 397-454]
  - parse_choice_response(text: str)                                  [lines 456-505]
```

### Dependencies
**Imports Used:**
```python
import re
import logging
from typing import Dict, List, Any, Optional
import json  # (inside extract_json_like method)
```

**Nothing imports this file** ✓

### Verification
- ✅ No imports found in any production files
- ✅ Not referenced in `app/engine/__init__.py`
- ✅ No test files depend on it
- ✅ Safe to delete

### Deletion Checklist
- [ ] Verify no imports exist
- [ ] Delete entire file
- [ ] Run test suite

---

## PHASE 1 ITEM #3: debug.py

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/utils/debug.py`
- **Line Range:** 1-268 (entire file)
- **Type:** Utility Classes and Functions
- **Size:** 268 lines, ~9 KB
- **Complexity:** Low - logging and decorators only

### Components to Delete
```python
Lines 1-14:    Module docstring and imports
Lines 17-54:   Class PerformanceMonitor(object):
  - __init__(self, name: str)                                         [lines 20-26]
  - __enter__(self)                                                   [lines 30-34]
  - __exit__(self, exc_type, exc_val, exc_tb)                         [lines 36-46]
  - elapsed property                                                  [lines 48-54]

Lines 57-74:   Function monitor_performance(func: Callable)           [wrapper decorator]

Lines 77-154:  Class StateTracker(object):
  - __init__(self)                                                    [lines 80-82]
  - log_state_change(component_type, component_id, change_type)      [lines 84-107]
  - log_generation(segment_id, choice_text, prompt_length, ...)      [lines 109-130]
  - get_summary()                                                     [lines 132-154]

Lines 157-227: Class DebugHelper(object):
  - format_segment_info(segment: Any)                                 [lines 160-182]
  - format_prompt_info(prompt: str, max_length: int = 500)            [lines 184-203]
  - format_response_info(response: Any)                               [lines 205-227]

Lines 230-252: Function enable_debug_logging(level: int = logging.DEBUG)

Lines 255-267: Function disable_debug_logging()
```

### Dependencies
**Imports Used:**
```python
import logging
import time
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime
```

**Nothing imports this file** ✓

### Verification
- ✅ No imports found in production code
- ✅ Not referenced in `app/utils/__init__.py`
- ✅ No tests import it
- ✅ Safe to delete

### Deletion Checklist
- [ ] Verify no imports
- [ ] Delete entire file
- [ ] Confirm no test failures

---

## PHASE 1 ITEM #4: debug_display.py

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/ui/debug_display.py`
- **Line Range:** 1-220 (entire file)
- **Type:** Display Functions (Module-level functions)
- **Size:** 220 lines, ~8 KB
- **Complexity:** Low - UI rendering only

### Components to Delete
```python
Lines 1-11:    Module docstring and imports
Lines 14-110:  Function display_segment_debug(segment)
Lines 113-164: Function display_next_context_debug(runner, segment)
Lines 167-220: Function prompt_choice_debug(segment, choices: List)
```

### Dependencies
**Imports Used:**
```python
import json
from typing import List
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt
import typer
from app.engine.segment_context_builder import SegmentContextBuilder  # (not critical)
```

**Nothing imports this file** ✓

### Verification
- ✅ Not imported anywhere (verified: only ui_debug_display.py and story_debug_display.py are used)
- ✅ Not referenced in `app/ui/__init__.py`
- ✅ Safe to delete

### Deletion Checklist
- [ ] Verify no imports exist
- [ ] Delete entire file
- [ ] Test CLI to ensure no errors

---

## PHASE 1 ITEMS #5-10: Six CLI Test Commands (in app/cli.py)

### Location & Metrics
- **File:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/cli.py`
- **Total Lines:** 602 lines to delete (6 command+async pairs)
- **Total Impact:** ~23 KB freed
- **Type:** CLI Commands (Typer decorators + async functions)

### Command #1: test_generation
**Lines:** 1079-1181 (102 lines)
```
Lines 1079-1175: async def test_generation_async(story_id: str)
Line  1176:      @app.command()
Lines 1177-1181: def test_generation(story_id: str = typer.Option(...))
```
**Dependencies:** Config, OpenRouterGenerator, OpenAIGenerator, Story, StoryRunner, ErrorHandler
**Usage:** None (debug/test command only)

### Command #2: test_world_generation
**Lines:** 1183-1274 (91 lines)
```
Lines 1183-1266: async def test_world_generation_async(story_id: str, user_input: str = "")
Line  1268:      @app.command()
Lines 1269-1274: def test_world_generation(...)
```
**Imports WorldGenerator** for testing

### Command #3: test_story_validation
**Lines:** 1276-1413 (137 lines)
```
Lines 1276-1406: async def test_story_validation_async(story_id: str)
Line  1408:      @app.command()
Lines 1409-1413: def test_story_validation(...)
```
**Imports StoryValidator** for testing

### Command #4: test_arc_generation
**Lines:** 1415-1502 (87 lines)
```
Lines 1415-1495: async def test_arc_generation_async(story_id: str, count: int = 3)
Line  1496:      @app.command()
Lines 1497-1502: def test_arc_generation(...)
```
**Imports ArcGenerator** for testing

### Command #5: test_character_generation
**Lines:** 1504-1595 (91 lines)
```
Lines 1504-1589: async def test_character_generation_async(story_id: str)
Line  1590:      @app.command()
Lines 1591-1595: def test_character_generation(...)
```
**Imports CharacterGenerator** for testing

### Command #6: test_protagonist_selection
**Lines:** 1597-1691 (94 lines)
```
Lines 1597-1684: async def test_protagonist_selection_async(story_id: str)
Line  1685:      @app.command()
Lines 1686-1691: def test_protagonist_selection(...)
```
**Imports ProtagonistSelector** for testing

### Verification for All 6 Commands
- ✅ Not called anywhere in production code
- ✅ These are debug/test utilities, not part of main CLI
- ✅ Removing them shrinks CLI from 1738 to 1136 lines
- ✅ No production code depends on them
- ✅ Safe to delete

### Deletion Checklist
- [ ] Delete lines 1079-1181 (test_generation)
- [ ] Delete lines 1183-1274 (test_world_generation)
- [ ] Delete lines 1276-1413 (test_story_validation)
- [ ] Delete lines 1415-1502 (test_arc_generation)
- [ ] Delete lines 1504-1595 (test_character_generation)
- [ ] Delete lines 1597-1691 (test_protagonist_selection)
- [ ] Verify remaining functions in cli.py still work
- [ ] Test CLI: `python -m app.cli --help`

---

## PHASE 1 ITEM #11: create_example_story()

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/utils/story_builder.py`
- **Line Range:** 367-500 (entire function)
- **Type:** Function
- **Size:** 133 lines
- **Complexity:** Medium - builds complex story structure

### Components to Delete
```python
Lines 367-500: def create_example_story() -> str:
  - Lines 373-378: Create StoryBuilder
  - Lines 380-396: Add worldbuilding
  - Lines 398-414: Add characters (Alex, Kai)
  - Lines 416-426: Add locations
  - Lines 428-436: Add opening segment
  - Lines 438-446: Add jungle_path segment
  - Lines 448-455: Add temple_entrance segment
  - Lines 457-470: Add choices for opening
  - Lines 472-484: Add choices for jungle_path
  - Lines 486-498: Add choices for temple_entrance
  - Line  500: Return builder.save()
```

### Dependencies
**Uses:**
```python
StoryBuilder (same file)
All story model classes (StorySegment, StoryChoice, etc.)
```

**Called By:** Nothing (verified via grep)

### Verification
- ✅ No calls found to this function
- ✅ Not exported from module
- ✅ Safe to delete

### Deletion Checklist
- [ ] Search for any calls to create_example_story()
- [ ] Delete entire function (lines 367-500)
- [ ] Verify StoryBuilder class still works correctly

---

## PHASE 2: REVIEW THEN DELETE

### Total Items: 2 files
### Impact: 225+ lines, 8+ KB
### Complexity: Medium - these have tests and dependencies

---

## PHASE 2 ITEM #1: auto_save_manager.py

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/services/auto_save_manager.py`
- **Total Lines:** 225+ (complete file)
- **Type:** Service Class
- **Size:** ~8 KB
- **Status:** Wrapper around SessionState.save()

### Purpose
Provides debounced auto-saving functionality for game sessions with configurable intervals.

### Main Components
```python
Class AutoSaveManager:
  DEBOUNCE_SECONDS = 10
  CLEANUP_OLDER_THAN_DAYS = 30
  _last_saves: Dict[str, datetime]
  _pending_saves: Dict[str, asyncio.Task]
  
  Methods:
  - should_save(cls, story_id: str) -> bool
  - async auto_save_async(cls, story_id: str, session: SessionState) -> bool
  - auto_save_sync(cls, story_id: str, session: SessionState) -> bool
  - get_auto_save_info(cls, story_id: str) -> dict
  - cleanup_old_saves(cls, days_old: Optional[int] = None) -> dict
```

### Where It's Used
```
/backend/tests/test_auto_save.py                    (imports: AutoSaveManager)
/backend/tests/test_auto_save_integration.py        (imports: AutoSaveManager)
/backend/tests/test_character_integration.py        (does NOT import this)
```

### Where It's Replaced By
**SessionState model** (`app/models/session_state.py`)
- SessionState.save() provides direct persistence
- Debouncing logic can be moved to API layer if needed
- No need for wrapper service when model handles its own persistence

### Review Actions
1. **Check if debouncing is still needed:**
   - Is debouncing important for API responses?
   - Can it be moved to route handler level?
   
2. **Verify SessionState.save() is sufficient:**
   - Does SessionState handle all the cleanup needed?
   - Are there any auto-save-specific requirements?

3. **Remove test files:**
   - Delete `test_auto_save.py`
   - Delete `test_auto_save_integration.py`

### Deletion Checklist
- [ ] Review test_auto_save.py to understand debounce requirements
- [ ] Check if debouncing logic should be in routes instead
- [ ] Verify SessionState persistence is sufficient
- [ ] Delete auto_save_manager.py
- [ ] Delete associated test files
- [ ] Run full test suite

---

## PHASE 2 ITEM #2: character_context_builder.py

### Location & Metrics
- **Full Path:** `/Users/artemmelnikov/Desktop/_stuff/infinite_story/backend/app/utils/character_context_builder.py`
- **Total Lines:** 255+ (complete file)
- **Type:** Utility Class
- **Size:** ~9 KB
- **Status:** Overlaps with SegmentContextBuilder

### Purpose
Builds rich character context for scene generation prompts.

### Main Components
```python
Class CharacterContextBuilder:
  Static Methods:
  - build_character_section(characters, current_segment_id, include_arcs, max_chars)
  - build_character_instructions(characters)
  - extract_character_updates_from_text(generated_text, characters, segment_id)
  
  Helper functions:
  - _extract_emotion_keywords()
  - _find_nearby_emotions()
```

### Where It's Used
```
/backend/tests/test_character_context_builder.py     (imports: CharacterContextBuilder)
/backend/tests/test_character_integration.py         (imports: CharacterContextBuilder)
```

### Where It's Replaced By
**SegmentContextBuilder** (`app/engine/segment_context_builder.py`)
- SegmentContextBuilder handles ALL context building (characters, locations, arcs, etc.)
- CharacterContextBuilder is a narrow, specialized version
- Consolidating to one builder would reduce duplication

### Review Actions
1. **Analyze SegmentContextBuilder:**
   - Does it already handle character context building?
   - What would need to be added/modified?

2. **Check for character-specific logic:**
   - Are there edge cases in CharacterContextBuilder not covered by SegmentContextBuilder?
   - Would moving to SegmentContextBuilder improve or worsen code quality?

3. **Update tests:**
   - Move test logic from test_character_context_builder.py to test_segment_context_builder.py
   - Or integrate into test_character_integration.py

### Deletion Checklist
- [ ] Review SegmentContextBuilder capabilities
- [ ] Check if all CharacterContextBuilder logic is covered
- [ ] Merge any missing logic into SegmentContextBuilder
- [ ] Update test imports
- [ ] Delete character_context_builder.py
- [ ] Delete test_character_context_builder.py
- [ ] Run full test suite, especially:
  - test_segment_context_builder.py
  - test_character_integration.py
  - test_generation_pipeline.py

---

## PHASE 3: RESPONSE MODEL AUDIT - NO ACTION NEEDED

### Summary
- **Total Response Models Analyzed:** 19 across 5 route files
- **Orphaned Models Found:** 0
- **Unused Endpoints Found:** 0
- **Recommendation:** No cleanup needed for Phase 3

### Detailed Findings

#### /app/routes/stories.py (240 lines)
7 Response Models - ALL USED
- StoryMetadata (lines 15-22) ✅
- TextBlock (lines 25-29) ✅
- Choice (lines 32-38) ✅
- SegmentResponse (lines 41-51) ✅
- StoryDetailResponse (lines 54-64) ✅
- ChoicesResponse (lines 67-71) ✅
- GenerateSceneRequest (lines 74-77) ✅

#### /app/routes/sessions.py (147 lines)
4 Response Models - ALL USED
- SessionStateRequest (lines 13-26) ✅
- SessionStateResponse (lines 29-32) ✅
- SessionSaveResponse (lines 35-39) ✅
- SessionDeleteResponse (lines 42-45) ✅

#### /app/routes/characters.py (200 lines)
4 Response Models - ALL USED
- CharacterStateResponse (lines 18-23) ✅
- CharacterResponse (lines 26-37) ✅
- CharacterListItemResponse (lines 40-46) ✅
- CharacterListResponse (lines 49-54) ✅

#### /app/routes/progress.py (94 lines)
1 Response Model - USED
- ProgressResponse (lines 13-30) ✅

#### /app/routes/reports.py (284 lines)
5 Response Models - ALL USED
- ContentReportRequest (lines 12-29) ✅
- ContentReportResponse (lines 32-37) ✅
- ContentReportDetailResponse (lines 40-51) ✅
- ReportListResponse (lines 54-60) ✅
- ReportSummaryResponse (lines 63-70) ✅

---

## SUMMARY & EXECUTION ORDER

### Phase 1 Execution (Delete Immediately)
**Total Lines:** 1,533  
**Total Size:** ~54 KB freed  
**Estimated Time:** 30 minutes  
**Risk Level:** ZERO (no dependencies)

**Delete in this order:**
1. Delete arc_compressor.py (301 lines)
2. Delete lenient_parser.py (506 lines)
3. Delete debug.py (268 lines)
4. Delete debug_display.py (220 lines)
5. Delete create_example_story() from story_builder.py (133 lines)
6. Delete 6 test commands from cli.py (602 lines)

**After deletion, run:**
```bash
pytest backend/tests/ -v  # Verify no test breakage
python -m app.cli --help   # Verify CLI still works
```

---

### Phase 2 Execution (Review Then Delete)
**Total Lines:** 225+  
**Total Size:** ~8 KB freed  
**Estimated Time:** 2-4 hours (review required)  
**Risk Level:** MEDIUM (has dependencies)

**Review sequence:**
1. Analyze auto_save_manager.py vs SessionState requirements
2. Analyze character_context_builder.py vs SegmentContextBuilder capabilities
3. Plan migration of logic if needed
4. Update tests
5. Delete files
6. Run full test suite

---

### Phase 3 Findings
**Action Required:** NONE  
**Status:** All response models in active use

---

## CHECKLIST FOR EXECUTION

### Pre-Deletion
- [ ] Create backup branch: `git checkout -b cleanup/phase-1-3`
- [ ] Verify all files with `git status`
- [ ] Run full test suite baseline: `pytest backend/tests/ -v`
- [ ] Document current state: `git log --oneline -5`

### Phase 1 Deletions
- [ ] Delete `/backend/app/engine/arc_compressor.py`
- [ ] Delete `/backend/app/engine/lenient_parser.py`
- [ ] Delete `/backend/app/utils/debug.py`
- [ ] Delete `/backend/app/ui/debug_display.py`
- [ ] Delete `create_example_story()` from `/backend/app/utils/story_builder.py` (lines 367-500)
- [ ] Delete 6 test commands from `/backend/app/cli.py` (1079-1691)

### Phase 1 Verification
- [ ] Run: `pytest backend/tests/ -v --tb=short`
- [ ] Run: `python -m app.cli --help` (no errors)
- [ ] Run: `python -m app.cli run-story --help` (works)
- [ ] Check for any `ImportError` messages

### Phase 2 Deletions (After Review)
- [ ] Review and plan auto_save_manager.py deletion
- [ ] Review and plan character_context_builder.py deletion
- [ ] Delete files
- [ ] Update test files

### Phase 2 Verification
- [ ] Run: `pytest backend/tests/ -v`
- [ ] Test session save/load: `pytest tests/test_session_state.py -v`
- [ ] Test character context: `pytest tests/test_segment_context_builder.py -v`

### Post-Deletion
- [ ] Commit changes: `git add . && git commit -m "cleanup: phase 1-3 code removal"`
- [ ] Push branch: `git push origin cleanup/phase-1-3`
- [ ] Create PR with this document as description
- [ ] Request review

---

## FILE DELETION VERIFICATION SCRIPT

```bash
#!/bin/bash
# Save as scripts/verify_cleanup.sh

echo "Verifying Phase 1 deletions..."

# Check files are deleted
for file in \
  "app/engine/arc_compressor.py" \
  "app/engine/lenient_parser.py" \
  "app/utils/debug.py" \
  "app/ui/debug_display.py"
do
  if [ -f "backend/$file" ]; then
    echo "❌ ERROR: $file still exists"
    exit 1
  else
    echo "✅ $file deleted"
  fi
done

# Check for orphaned imports
echo ""
echo "Checking for orphaned imports..."
if grep -r "arc_compressor\|lenient_parser\|from.*debug import\|debug_display" \
     backend/app --include="*.py"; then
  echo "❌ Found remaining imports"
  exit 1
else
  echo "✅ No orphaned imports found"
fi

echo ""
echo "Running test suite..."
cd backend
python -m pytest tests/ -v --tb=short || exit 1

echo ""
echo "✅ All verifications passed!"
```

---

**Document Version:** 1.0  
**Last Updated:** March 3, 2026  
**Created By:** Code Analysis System  
**Status:** Ready for Execution
