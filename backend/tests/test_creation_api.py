"""Tests for story creation API endpoints."""

import pytest
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.models.story_base import LOCAL_DATA_DIR


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def cleanup_created_story():
    """Cleanup any story created during tests."""
    story_ids = []

    def track(story_id):
        story_ids.append(story_id)
        return story_id

    yield track

    for sid in story_ids:
        story_dir = LOCAL_DATA_DIR / sid
        if story_dir.exists():
            shutil.rmtree(story_dir)


class TestCreateStoryEndpoint:
    """Tests for POST /api/stories/create."""

    def test_create_requires_fields(self, client):
        """Validation requires story_id, title, description."""
        response = client.post("/api/stories/create", json={})
        assert response.status_code == 422

    def test_create_requires_title(self, client):
        response = client.post("/api/stories/create", json={
            "story_id": "x",
            "description": "d",
        })
        assert response.status_code == 422

    def test_create_duplicate_existing_story(self, client, cleanup_created_story):
        """Cannot create story if it already exists on disk."""
        sid = cleanup_created_story("test_dup_story")
        # Create story dir to simulate existing story
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

        response = client.post("/api/stories/create", json={
            "story_id": sid,
            "title": "Test",
            "description": "Desc",
            "genre": "Fantasy",
        })
        data = response.json()
        assert data["success"] is False
        assert "already exists" in data["error"]


class TestCreationStatusEndpoint:
    """Tests for GET /api/stories/create/{story_id}/status."""

    def test_status_not_found(self, client):
        response = client.get("/api/stories/create/nonexistent_xyz/status")
        data = response.json()
        assert data["success"] is False
        assert "no creation job" in data["error"].lower()


class TestDeleteStoryEndpoint:
    """Tests for DELETE /api/stories/{story_id}."""

    def test_delete_not_found(self, client):
        response = client.delete("/api/stories/nonexistent_story_xyz")
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()

    def test_delete_existing(self, client, cleanup_created_story):
        sid = "test_delete_story"
        story_dir = LOCAL_DATA_DIR / sid
        story_dir.mkdir(parents=True, exist_ok=True)
        (story_dir / "marker.txt").write_text("test")

        response = client.delete(f"/api/stories/{sid}")
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True
        assert not story_dir.exists()


class TestCreationStreamEndpoint:
    """Tests for GET /api/stories/create/{story_id}/stream."""

    def test_stream_no_job(self, client):
        """SSE stream returns error for unknown story."""
        response = client.get("/api/stories/create/nonexistent_xyz/stream")
        assert response.status_code == 200
        # Should contain error data
        text = response.text
        assert "error" in text.lower() or "No creation job" in text
