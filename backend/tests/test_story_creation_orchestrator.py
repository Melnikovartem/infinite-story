"""Tests for StoryCreationOrchestrator."""

import pytest
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.engine.story_creation_orchestrator import (
    StoryCreationOrchestrator,
    StepProgress,
    CreationResult,
)
from app.models.story_base import LOCAL_DATA_DIR


@pytest.fixture
def cleanup_story():
    """Cleanup any story created during tests."""
    story_ids = []

    def track(sid):
        story_ids.append(sid)
        return sid

    yield track

    for sid in story_ids:
        story_dir = LOCAL_DATA_DIR / sid
        if story_dir.exists():
            shutil.rmtree(story_dir)


@pytest.fixture
def mock_generator():
    """Create a mock TextGenerator."""
    gen = AsyncMock()
    gen.generate_structured = AsyncMock(return_value={
        "text_blocks": [
            {"type": "narrator_describing", "content": "Test scene content.", "emotion": "neutral"}
        ],
        "short_description": "Test opening",
        "atmosphere": "mysterious",
        "time_of_day": "evening",
        "weather": "clear",
        "key_items": [],
        "characters_present": [],
        "locations_present": [],
        "choice_1": "Go forward into the unknown",
        "choice_2": "Stay and investigate the area",
    })
    return gen


class TestStepProgress:
    def test_step_progress_creation(self):
        p = StepProgress(step=0, name="Test", status="running", message="hello")
        assert p.step == 0
        assert p.name == "Test"
        assert p.status == "running"
        assert p.message == "hello"

    def test_step_progress_defaults(self):
        p = StepProgress(step=1, name="X", status="pending")
        assert p.message == ""
        assert p.detail is None


class TestCreationResult:
    def test_default_values(self):
        r = CreationResult(success=False, story_id="test")
        assert r.success is False
        assert r.story is None
        assert r.error is None
        assert r.steps_completed == 0
        assert r.steps_total == 11
        assert r.artifacts == {}


class TestOrchestratorProgressCallback:
    def test_callback_receives_progress(self, mock_generator):
        progress_log = []

        def on_progress(p: StepProgress):
            progress_log.append(p)

        orch = StoryCreationOrchestrator(
            generator=mock_generator,
            progress_callback=on_progress,
        )

        orch._emit(0, "Test Step", "running", "starting")
        assert len(progress_log) == 1
        assert progress_log[0].step == 0
        assert progress_log[0].status == "running"

    def test_no_callback_no_error(self, mock_generator):
        """No callback should not raise."""
        orch = StoryCreationOrchestrator(generator=mock_generator)
        orch._emit(0, "Test", "completed", "ok")


class TestOrchestratorDuplicateCheck:
    @pytest.mark.asyncio
    async def test_rejects_existing_story(self, mock_generator, cleanup_story):
        """Orchestrator should reject creation if story already exists."""
        sid = cleanup_story("test_orch_dup")
        # Create the story on disk
        story_dir = LOCAL_DATA_DIR / sid / "story"
        story_dir.mkdir(parents=True, exist_ok=True)
        import json
        with open(story_dir / f"{sid}.json", "w") as f:
            json.dump({
                "id": sid, "story_id": sid, "title": "T", "description": "D",
                "genre": "Fantasy", "start_segment_id": "opening",
                "created_at": "2024-01-01T00:00:00+00:00",
                "updated_at": "2024-01-01T00:00:00+00:00",
            }, f)

        orch = StoryCreationOrchestrator(generator=mock_generator)
        result = await orch.create_story(
            story_id=sid,
            title="Test",
            description="Desc",
            genre="Fantasy",
        )
        assert result.success is False
        assert "already exists" in result.error


class TestGetCreationSummary:
    def test_summary_from_result(self, mock_generator):
        orch = StoryCreationOrchestrator(generator=mock_generator)

        result = CreationResult(
            success=True,
            story_id="test",
            steps_completed=10,
            artifacts={
                "factions": [1, 2, 3],
                "locations": [1, 2],
                "arcs": [1],
                "characters": [1, 2, 3, 4],
                "choices": [1, 2],
                "protagonist": object(),
                "magic_system": None,
            },
        )

        summary = orch.get_creation_summary(result)
        assert summary["story_id"] == "test"
        assert summary["success"] is True
        assert summary["steps_completed"] == 10
        assert summary["summary"]["factions"] == 3
        assert summary["summary"]["locations"] == 2
        assert summary["summary"]["arcs"] == 1
        assert summary["summary"]["characters"] == 4
        assert summary["summary"]["choices"] == 2
        assert summary["summary"]["has_protagonist"] is True
        assert summary["summary"]["has_magic_system"] is False
