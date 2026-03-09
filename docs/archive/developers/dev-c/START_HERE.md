# Welcome, Developer C!

**Epic:** Data Layer Foundation (E0)  
**Duration:** 1 week  
**Your Role:** Mid-level Engineer, focus on scripts & testing

---

## Your Mission

You're the ops and testing specialist on the foundation team. You'll:

1. **E0-5** (2 days): Write a migration script
   - Convert existing v1 stories to v2 format
   - Add default values for new fields
   - Create backup mechanism
   - Validate data integrity
   - Test on real `veil_of_thornreach` data

2. **E0-6** (1 day): Build test infrastructure
   - Create pytest fixtures for all teams to use
   - Create factory functions for test data
   - Setup async testing
   - Setup temporary directories for tests

Your work ensures E0 is done right and E1/E2/E3/E4 can test properly.

---

## First Steps

1. **Read ONBOARDING.md**
2. **Read EPIC_0_DATA_LAYER.md** (focus on E0-5 & E0-6)
3. **Check out existing tests** (`backend/tests/`) to understand patterns

---

## Your Tasks

### E0-5: Migration Script (2 days)

**File:** `backend/scripts/migrate_v1_to_v2.py` (NEW)

See `EPIC_0_DATA_LAYER.md` section "E0-5" for pseudocode and examples.

**Steps:**
1. Load all existing v1 segments
2. Add v2 fields with sensible defaults
3. Create default EpisodeRecap for episode 1
4. Create default StoryArc
5. Backup data before migrating
6. Validate no data loss
7. Create rollback script
8. Test on real `veil_of_thornreach` story

**Acceptance Criteria:**
- [ ] Script loads v1 segments
- [ ] All v2 fields added
- [ ] Default EpisodeRecap created
- [ ] Default StoryArc created
- [ ] Backup created before migration
- [ ] Validation checks pass
- [ ] Rollback script works
- [ ] Tested on real data
- [ ] Unit tests (2+)

### E0-6: Test Infrastructure (1 day)

**Files:** 
- `backend/tests/conftest.py` (ENHANCE)
- `backend/tests/fixtures/` (CREATE)

See `EPIC_0_DATA_LAYER.md` section "E0-6" for code examples.

**What to Create:**
- Pytest fixtures: `sample_story`, `sample_segment`, `sample_choice`
- Async testing setup
- Mock generators
- Temporary data directories
- Factory functions: `factory_story()`, `factory_segment()`

**Acceptance Criteria:**
- [ ] conftest.py has 5+ fixtures
- [ ] Factory functions created
- [ ] Async tests working
- [ ] Mock generators available
- [ ] Temp directories working
- [ ] All E0 tests still passing

---

## Key Files

```
backend/tests/
  ├── conftest.py         ← YOU ENHANCE
  ├── test_story_models.py ← Uses your fixtures
  └── fixtures/           ← YOU CREATE

backend/scripts/
  └── migrate_v1_to_v2.py ← YOU CREATE
```

---

## Testing Resources

- `EPIC_0_DATA_LAYER.md` → E0-6 section has fixture examples
- `backend/tests/` → Look at existing fixtures for patterns
- `pytest documentation` → For advanced fixture patterns

---

## Migration Pseudocode

```python
# Load existing data
all_segments = load_from_disk("v1")

# Transform
for segment in all_segments:
    segment['episode_number'] = 1
    segment['status'] = 'generated'
    segment['character_states'] = {}
    segment['change_notes'] = []
    # ... add other v2 fields

# Backup
backup_dir = create_backup()

# Save in v2 format
save_to_disk(all_segments)

# Validate
assert no_data_loss()
assert all_fields_present()

# Create rollback option
create_rollback_script(backup_dir)
```

---

## Collaboration

- **Ask Dev-A** (your lead) for questions
- **Pair with Dev-A or Dev-B** on migration testing
- **Daily standup** with the team

---

## Commits

```bash
git commit -m "E0-5: create migration script v1 to v2 with rollback"
git commit -m "E0-6: setup pytest fixtures and test infrastructure"
```

---

## Next Action

→ Open `EPIC_0_DATA_LAYER.md` section E0-5. Start with migration script.

You're building the foundation for everyone else. Great responsibility! 🏗️
