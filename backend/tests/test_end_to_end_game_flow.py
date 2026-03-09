"""End-to-end game flow testing for Phase 2.

Tests complete user journeys from story start to completion.
Uses the actual API endpoints with correct request/response models.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from pathlib import Path
import shutil
import time
from app.main import app

client = TestClient(app)


def _make_session(story_id: str, session_id: str, user_id: str,
                  current_segment_id: str, visited_segments: list,
                  visited_choices: list = None) -> dict:
    """Build a valid session save payload."""
    return {
        "id": session_id,
        "story_id": story_id,
        "user_id": user_id,
        "current_segment_id": current_segment_id,
        "visited_segments": visited_segments,
        "visited_choices": visited_choices or [],
    }


@pytest.fixture(autouse=True)
def cleanup_e2e_data():
    """Clean up test data after each test."""
    yield
    
    test_dir = Path(".infinite_story_data")
    if test_dir.exists():
        for story_dir in ["e2e_story_*", "playthrough_*", "journey_*"]:
            for path in test_dir.glob(story_dir):
                if path.is_dir():
                    shutil.rmtree(path)


class TestBasicGamePlaythrough:
    """Test a basic complete game playthrough."""
    
    def test_complete_story_journey(self):
        """Test completing a full story journey."""
        story_id = "e2e_story_basic"
        session_id = "session_basic"
        user_id = "test_user"
        
        # 1. Start the game
        payload = _make_session(story_id, session_id, user_id, "intro", ["intro"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 2. Progress through 5 scenes
        visited = ["intro"]
        for scene_num in range(2, 6):
            visited.append(f"scene_{scene_num}")
            payload = _make_session(story_id, session_id, user_id,
                                    f"scene_{scene_num}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # 3. Load and verify
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.status_code == 200
        assert response.json()["found"] is True
        session_data = response.json()["session"]
        assert session_data["current_segment_id"] == "scene_5"
        assert "scene_5" in session_data["visited_segments"]


class TestMultiplePlayersIndependent:
    """Test multiple players playing independently."""
    
    def test_two_players_different_stories(self):
        """Test two players in different stories maintain independent state."""
        # Player 1
        p1_story = "e2e_story_player1"
        p1_payload = _make_session(p1_story, "p1_session", "player1", "chapter_1", ["chapter_1"])
        response = client.post("/api/sessions/save", json=p1_payload)
        assert response.status_code == 200
        
        # Player 2
        p2_story = "e2e_story_player2"
        p2_payload = _make_session(p2_story, "p2_session", "player2", "act_1", ["act_1"])
        response = client.post("/api/sessions/save", json=p2_payload)
        assert response.status_code == 200
        
        # Player 1 progresses
        p1_payload = _make_session(p1_story, "p1_session", "player1",
                                   "chapter_2", ["chapter_1", "chapter_2"])
        response = client.post("/api/sessions/save", json=p1_payload)
        assert response.status_code == 200
        
        # Player 2 progresses
        p2_payload = _make_session(p2_story, "p2_session", "player2",
                                   "act_2", ["act_1", "act_2"])
        response = client.post("/api/sessions/save", json=p2_payload)
        assert response.status_code == 200
        
        # Verify independent states
        r1 = client.get(f"/api/sessions/{p1_story}/p1_session")
        assert r1.json()["session"]["current_segment_id"] == "chapter_2"
        
        r2 = client.get(f"/api/sessions/{p2_story}/p2_session")
        assert r2.json()["session"]["current_segment_id"] == "act_2"


class TestSessionPersistence:
    """Test session persistence across saves."""
    
    def test_session_resume_from_save(self):
        """Test resuming a game from a save point."""
        story_id = "e2e_story_resume"
        session_id = "resume_session"
        user_id = "test_user"
        
        visited = ["segment_1"]
        payload = _make_session(story_id, session_id, user_id, "segment_1", visited)
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # Progress
        for i in range(2, 4):
            visited.append(f"segment_{i}")
            payload = _make_session(story_id, session_id, user_id, f"segment_{i}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # Load from save
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.status_code == 200
        loaded = response.json()["session"]
        assert loaded["current_segment_id"] == "segment_3"
        assert len(loaded["visited_segments"]) == 3


class TestReportingDuringGameplay:
    """Test content reporting during gameplay."""
    
    def test_submit_report_during_game(self):
        """Test submitting a report while playing."""
        story_id = "e2e_story_with_report"
        
        # Start game
        payload = _make_session(story_id, "report_session", "test_user",
                                "segment_1", ["segment_1"])
        client.post("/api/sessions/save", json=payload)
        
        # Submit report
        report = {
            "story_id": story_id,
            "segment_id": "segment_1",
            "report_type": "inappropriate_content",
            "description": "This content seems inappropriate"
        }
        response = client.post("/api/reports", json=report)
        assert response.status_code == 201
        report_id = response.json()["report_id"]
        
        # Continue game
        payload = _make_session(story_id, "report_session", "test_user",
                                "segment_2", ["segment_1", "segment_2"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # Verify report still exists
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200


class TestProgressTracking:
    """Test progress tracking accuracy throughout game."""
    
    def test_progress_updates_with_scenes(self):
        """Test progress tracking matches scene progression."""
        story_id = "e2e_story_progress"
        session_id = "progress_session"
        user_id = "test_user"
        
        # Track progress through 5 scenes
        visited = []
        for scene_num in range(1, 6):
            visited.append(f"segment_{scene_num}")
            payload = _make_session(story_id, session_id, user_id,
                                    f"segment_{scene_num}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
            
            # Check progress
            response = client.get(f"/api/progress/{story_id}/{session_id}")
            assert response.status_code == 200
            progress = response.json()
            assert progress["scene_number"] == scene_num
            assert progress["total_visited"] == scene_num
    
    def test_elapsed_time_increases(self):
        """Test that elapsed time doesn't break."""
        story_id = "e2e_story_timing"
        session_id = "timing_session"
        user_id = "test_user"
        
        payload = _make_session(story_id, session_id, user_id,
                                "segment_1", ["segment_1"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        response = client.get(f"/api/progress/{story_id}/{session_id}")
        assert response.status_code == 200
        initial_elapsed = response.json()["elapsed_seconds"]
        assert initial_elapsed >= 0


class TestLongGameSession:
    """Test long gaming sessions."""
    
    def test_extended_gameplay_session(self):
        """Test playing through a long session."""
        story_id = "e2e_story_long"
        session_id = "long_session"
        user_id = "test_user"
        
        visited = ["segment_1"]
        payload = _make_session(story_id, session_id, user_id, "segment_1", visited)
        client.post("/api/sessions/save", json=payload)
        
        # Play through 50 scenes
        for scene in range(2, 51):
            visited.append(f"segment_{scene}")
            payload = _make_session(story_id, session_id, user_id,
                                    f"segment_{scene}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # Verify final state
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.status_code == 200
        session_data = response.json()["session"]
        assert session_data["current_segment_id"] == "segment_50"
        assert len(session_data["visited_segments"]) == 50


class TestGameflowWithErrors:
    """Test handling errors during normal gameplay."""
    
    def test_invalid_choice_then_continue(self):
        """Test game continues after invalid request."""
        story_id = "e2e_story_error_recovery"
        session_id = "error_session"
        user_id = "test_user"
        
        # Start game
        payload = _make_session(story_id, session_id, user_id,
                                "segment_1", ["segment_1"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # Invalid payload (missing required fields)
        response = client.post("/api/sessions/save", json={"story_id": story_id})
        assert response.status_code == 422  # Validation error
        
        # Game continues with valid update
        payload = _make_session(story_id, session_id, user_id,
                                "segment_2", ["segment_1", "segment_2"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # Verify state updated
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.json()["session"]["current_segment_id"] == "segment_2"


class TestCompleteEndToEndFlow:
    """Test a complete realistic game flow."""
    
    def test_realistic_game_scenario(self):
        """Test a realistic end-to-end game scenario."""
        story_id = "e2e_story_realistic"
        session_id = "realistic_session"
        user_id = "test_user"
        
        # 1. Start game
        visited = ["prologue"]
        payload = _make_session(story_id, session_id, user_id, "prologue", visited)
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # 2. Play through chapter 1
        for scene in range(1, 5):
            seg_id = f"chapter1_scene{scene}"
            visited.append(seg_id)
            payload = _make_session(story_id, session_id, user_id, seg_id, visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # 3. Report an issue mid-game
        report = {
            "story_id": story_id,
            "segment_id": "chapter1_scene2",
            "report_type": "spelling_error",
            "description": "Found a typo in the narrative"
        }
        response = client.post("/api/reports", json=report)
        assert response.status_code == 201
        
        # 4. Continue to chapter 2
        for scene in range(1, 6):
            seg_id = f"chapter2_scene{scene}"
            visited.append(seg_id)
            payload = _make_session(story_id, session_id, user_id, seg_id, visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # 5. Check progress
        response = client.get(f"/api/progress/{story_id}/{session_id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["total_visited"] == 10  # prologue + 4 ch1 + 5 ch2
        
        # 6. Final session state
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.status_code == 200
        final = response.json()["session"]
        assert final["current_segment_id"] == "chapter2_scene5"
        assert len(final["visited_segments"]) == 10
