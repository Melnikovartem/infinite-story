"""Integration tests for story and segment endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import json
import shutil
from app.main import app
from app.models.story_base import LOCAL_DATA_DIR
from app.models.story import Story
from app.models.story_segment import StorySegment
from app.models.story_choice import StoryChoice


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_story_data():
    """Create test story data on disk."""
    story_id = "test_story_integration"
    story_dir = LOCAL_DATA_DIR / story_id
    
    # Clean up before
    if story_dir.exists():
        shutil.rmtree(story_dir)
    
    # Create story directory
    story_file_dir = story_dir / "story"
    story_file_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test story
    story_data = {
        "id": story_id,
        "story_id": story_id,
        "title": "Test Story",
        "description": "A test story for integration testing",
        "genre": "Fantasy",
        "start_segment_id": "opening_scene",
        "created_at": "2024-02-28T10:00:00+00:00",
        "updated_at": "2024-02-28T10:00:00+00:00",
    }
    
    with open(story_file_dir / f"{story_id}.json", "w") as f:
        json.dump(story_data, f)
    
    # Create test segment
    segment_dir = story_dir / "storysegment"
    segment_dir.mkdir(parents=True, exist_ok=True)
    
    segment_data = {
        "id": "opening_scene",
        "story_id": story_id,
        "short_description": "The beginning of the adventure",
        "atmosphere": "Mysterious and intriguing",
        "time_of_day": "Evening",
        "weather": "Cloudy",
        "text_blocks": [
            {
                "type": "narrator_describing",
                "content": "You find yourself in a strange place..."
            }
        ],
        "characters_present": ["hero"],
        "locations_present": ["forest"],
        "characters": [],
        "locations": [],
        "characters_running_status": [],
        "locations_running_status": [],
        "created_at": "2024-02-28T10:00:00+00:00",
        "updated_at": "2024-02-28T10:00:00+00:00",
    }
    
    with open(segment_dir / "opening_scene.json", "w") as f:
        json.dump(segment_data, f)
    
    # Create test choices
    choices_dir = story_dir / "storychoice"
    choices_dir.mkdir(parents=True, exist_ok=True)
    
    choice1_data = {
        "id": "choice_1",
        "story_id": story_id,
        "from_segment_id": "opening_scene",
        "to_segment_id": "next_scene",
        "text": "Go forward",
        "clicks_logged": 0,
        "clicks_anonymous": 0,
        "flags": {"nsfw": False, "violent": False},
        "created_at": "2024-02-28T10:00:00+00:00",
        "updated_at": "2024-02-28T10:00:00+00:00",
    }
    
    choice2_data = {
        "id": "choice_2",
        "story_id": story_id,
        "from_segment_id": "opening_scene",
        "to_segment_id": "alternate_scene",
        "text": "Turn back",
        "clicks_logged": 0,
        "clicks_anonymous": 0,
        "flags": {"nsfw": False, "violent": False},
        "created_at": "2024-02-28T10:00:00+00:00",
        "updated_at": "2024-02-28T10:00:00+00:00",
    }
    
    with open(choices_dir / "choice_1.json", "w") as f:
        json.dump(choice1_data, f)
    
    with open(choices_dir / "choice_2.json", "w") as f:
        json.dump(choice2_data, f)
    
    yield story_id
    
    # Clean up after
    if story_dir.exists():
        shutil.rmtree(story_dir)


def test_list_stories(client, test_story_data):
    """Test listing all stories."""
    response = client.get("/api/stories")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stories" in data["data"]
    assert "count" in data["data"]
    assert len(data["data"]["stories"]) > 0


def test_list_stories_contains_test_story(client, test_story_data):
    """Test that list includes our test story."""
    response = client.get("/api/stories")
    assert response.status_code == 200
    data = response.json()
    stories = data["data"]["stories"]
    story_ids = [s["id"] for s in stories]
    assert test_story_data in story_ids


def test_get_story_detail(client, test_story_data):
    """Test getting story details."""
    response = client.get(f"/api/stories/{test_story_data}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    story = data["data"]
    assert story["id"] == test_story_data
    assert story["title"] == "Test Story"
    assert story["description"] == "A test story for integration testing"
    assert story["genre"] == "Fantasy"


def test_get_story_detail_not_found(client):
    """Test getting non-existent story."""
    response = client.get("/api/stories/nonexistent_story")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_get_segment(client, test_story_data):
    """Test getting a segment with choices."""
    response = client.get(
        f"/api/segments/opening_scene?story_id={test_story_data}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    result = data["data"]
    
    # Check segment data
    assert "segment" in result
    segment = result["segment"]
    assert segment["id"] == "opening_scene"
    assert segment["story_id"] == test_story_data
    assert segment["short_description"] == "The beginning of the adventure"
    
    # Check choices
    assert "choices" in result
    choices = result["choices"]
    assert "top" in choices
    assert "all" in choices
    assert len(choices["all"]) == 2


def test_get_segment_not_found(client, test_story_data):
    """Test getting non-existent segment."""
    response = client.get(
        f"/api/segments/nonexistent_segment?story_id={test_story_data}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_generate_next_scene_endpoint_exists(client, test_story_data):
    """Test that the generate next scene endpoint exists and validates input.
    
    We test with a nonexistent story to avoid triggering real AI generation.
    """
    # Test with missing required field - should get 422
    response = client.post(
        f"/api/segments/opening_scene/next?story_id={test_story_data}",
        json={}
    )
    assert response.status_code == 422  # Validation error - choice_text is required

    # Test with valid body but nonexistent story - should get error response
    response = client.post(
        f"/api/segments/opening_scene/next?story_id=nonexistent_story",
        json={"choice_text": "Continue exploring"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_navigate_to_choice_endpoint_exists(client, test_story_data):
    """Test that the navigate to choice endpoint exists."""
    # Test with nonexistent story
    response = client.post(
        f"/api/segments/opening_scene/choice/choice_1?story_id=nonexistent_story"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "not found" in data["error"].lower()


def test_navigate_to_choice_validates_segment(client, test_story_data):
    """Test that navigate validates choice belongs to segment."""
    # choice_1 belongs to opening_scene, not some_other_segment
    response = client.post(
        f"/api/segments/some_other_segment/choice/choice_1?story_id={test_story_data}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False


def test_api_docs_include_stories_routes(client):
    """Test that API docs include stories routes."""
    response = client.get("/api/docs")
    assert response.status_code == 200
    # The docs page should load without errors
    assert "html" in response.text.lower() or "swagger" in response.text.lower()
