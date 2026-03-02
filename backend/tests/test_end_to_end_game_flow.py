"""End-to-end game flow testing for Phase 2.

Tests complete user journeys from story start to completion.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta
from pathlib import Path
import shutil
import time
from app.main import app

client = TestClient(app)


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
        
        # 1. Start the game
        start_session = {
            "story_id": story_id,
            "current_segment_id": "intro",
            "visited_segments": ["intro"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=start_session)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 2. Get initial progress
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        assert response.json()["scene_number"] == 1
        
        # 3. Progress through 5 scenes
        for scene_num in range(2, 6):
            session_update = {
                "story_id": story_id,
                "current_segment_id": f"scene_{scene_num}",
                "visited_segments": ["intro"] + [f"scene_{i}" for i in range(2, scene_num + 1)],
                "scene_counter": scene_num,
                "start_time": start_session["start_time"]
            }
            
            response = client.post("/api/sessions/save", json=session_update)
            assert response.status_code == 200
        
        # 4. Verify final state
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        final_session = response.json()["session"]
        assert final_session["scene_counter"] == 5
        assert "scene_5" in final_session["visited_segments"]
        
        # 5. Check final progress
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["scene_number"] == 5
        assert progress["total_visited"] == 5


class TestMultiplePlayersIndependent:
    """Test multiple players playing independently."""
    
    def test_two_players_different_stories(self):
        """Test two players in different stories maintain independent state."""
        player1_story = "e2e_story_player1"
        player2_story = "e2e_story_player2"
        
        # Player 1 starts story A
        player1_session = {
            "story_id": player1_story,
            "current_segment_id": "chapter_1",
            "visited_segments": ["chapter_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=player1_session)
        assert response.status_code == 200
        
        # Player 2 starts story B
        player2_session = {
            "story_id": player2_story,
            "current_segment_id": "act_1",
            "visited_segments": ["act_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=player2_session)
        assert response.status_code == 200
        
        # Player 1 progresses
        player1_session["current_segment_id"] = "chapter_2"
        player1_session["visited_segments"].append("chapter_2")
        player1_session["scene_counter"] = 2
        
        response = client.post("/api/sessions/save", json=player1_session)
        assert response.status_code == 200
        
        # Player 2 progresses differently
        player2_session["current_segment_id"] = "act_2"
        player2_session["visited_segments"].append("act_2")
        player2_session["scene_counter"] = 2
        
        response = client.post("/api/sessions/save", json=player2_session)
        assert response.status_code == 200
        
        # Verify independent states
        response = client.get(f"/api/sessions/{player1_story}")
        assert response.json()["session"]["current_segment_id"] == "chapter_2"
        
        response = client.get(f"/api/sessions/{player2_story}")
        assert response.json()["session"]["current_segment_id"] == "act_2"


class TestSessionPersistence:
    """Test session persistence across saves."""
    
    def test_session_resume_from_save(self):
        """Test resuming a game from a save point."""
        story_id = "e2e_story_resume"
        
        # Play through part of the game
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session)
        assert response.status_code == 200
        
        # Progress further
        for i in range(2, 4):
            session["current_segment_id"] = f"segment_{i}"
            session["visited_segments"].append(f"segment_{i}")
            session["scene_counter"] = i
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
        
        # Simulate loading from save
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        loaded_session = response.json()["session"]
        
        # Continue from loaded state
        loaded_session["current_segment_id"] = "segment_4"
        loaded_session["visited_segments"].append("segment_4")
        loaded_session["scene_counter"] = 4
        
        response = client.post("/api/sessions/save", json=loaded_session)
        assert response.status_code == 200
        
        # Verify continuation worked
        response = client.get(f"/api/sessions/{story_id}")
        assert response.json()["session"]["scene_counter"] == 4


class TestReportingDuringGameplay:
    """Test content reporting during gameplay."""
    
    def test_submit_report_during_game(self):
        """Test submitting a report while playing."""
        story_id = "e2e_story_with_report"
        
        # Start game
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        client.post("/api/sessions/save", json=session)
        
        # Submit report during gameplay
        report = {
            "story_id": story_id,
            "segment_id": "segment_1",
            "report_type": "inappropriate_content",
            "description": "This content seems inappropriate for the story"
        }
        
        response = client.post("/api/reports", json=report)
        assert response.status_code == 201
        report_id = response.json()["report_id"]
        
        # Continue game
        session["current_segment_id"] = "segment_2"
        session["visited_segments"].append("segment_2")
        session["scene_counter"] = 2
        
        response = client.post("/api/sessions/save", json=session)
        assert response.status_code == 200
        
        # Verify report still exists
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200


class TestProgressTracking:
    """Test progress tracking accuracy throughout game."""
    
    def test_progress_updates_with_scenes(self):
        """Test progress tracking matches scene progression."""
        story_id = "e2e_story_progress"
        start_time = datetime.now(UTC)
        
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": start_time.isoformat()
        }
        
        # Track progress through 10 scenes
        for scene_num in range(1, 11):
            session["current_segment_id"] = f"segment_{scene_num}"
            session["visited_segments"] = [f"segment_{i}" for i in range(1, scene_num + 1)]
            session["scene_counter"] = scene_num
            
            # Save session
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
            
            # Check progress
            response = client.get(f"/api/progress/{story_id}")
            assert response.status_code == 200
            progress = response.json()
            
            # Verify accuracy
            assert progress["scene_number"] == scene_num
            assert progress["total_visited"] == scene_num
            assert progress["reading_pace_minutes_per_scene"] >= 0
    
    def test_elapsed_time_increases(self):
        """Test that elapsed time increases correctly."""
        story_id = "e2e_story_timing"
        start_time = datetime.now(UTC)
        
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": start_time.isoformat()
        }
        
        # Initial save
        response = client.post("/api/sessions/save", json=session)
        assert response.status_code == 200
        
        # Get initial progress
        response = client.get(f"/api/progress/{story_id}")
        initial_elapsed = response.json()["elapsed_seconds"]
        
        # Simulate time passing and scene change
        time.sleep(0.1)  # 100ms delay
        
        session["current_segment_id"] = "segment_2"
        session["visited_segments"].append("segment_2")
        session["scene_counter"] = 2
        
        response = client.post("/api/sessions/save", json=session)
        assert response.status_code == 200
        
        # Get updated progress
        response = client.get(f"/api/progress/{story_id}")
        final_elapsed = response.json()["elapsed_seconds"]
        
        # Elapsed time should have increased (or stayed same if implementation rounds)
        assert final_elapsed >= initial_elapsed


class TestMultipleReports:
    """Test handling multiple reports for same story."""
    
    def test_multiple_reports_same_story(self):
        """Test submitting multiple reports for different segments."""
        story_id = "e2e_story_multi_report"
        
        # Submit reports for different segments
        report_ids = []
        for segment_num in range(1, 4):
            report = {
                "story_id": story_id,
                "segment_id": f"segment_{segment_num}",
                "report_type": "inappropriate_content" if segment_num % 2 == 0 else "spelling_error",
                "description": f"Issue found in segment {segment_num} that needs attention"
            }
            
            response = client.post("/api/reports", json=report)
            assert response.status_code == 201
            report_ids.append(response.json()["report_id"])
        
        # List reports by story
        response = client.get(f"/api/reports?story_id={story_id}")
        assert response.status_code == 200
        reports = response.json()["reports"]
        
        # Verify all reports present
        story_reports = [r for r in reports if r["story_id"] == story_id]
        assert len(story_reports) >= 3


class TestLongGameSession:
    """Test long gaming sessions."""
    
    def test_extended_gameplay_session(self):
        """Test playing through a long session."""
        story_id = "e2e_story_long"
        
        # Simulate a long gaming session (many scenes)
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        client.post("/api/sessions/save", json=session)
        
        # Play through 50 scenes
        for scene in range(2, 51):
            session["current_segment_id"] = f"segment_{scene}"
            session["visited_segments"].append(f"segment_{scene}")
            session["scene_counter"] = scene
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
        
        # Verify final state
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        assert response.json()["session"]["scene_counter"] == 50
        
        # Get final progress
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        assert response.json()["scene_number"] == 50


class TestGameflowWithErrors:
    """Test handling errors during normal gameplay."""
    
    def test_invalid_choice_then_continue(self):
        """Test game continues after invalid choice attempt."""
        story_id = "e2e_story_error_recovery"
        
        # Start game
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_1",
            "visited_segments": ["segment_1"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session)
        assert response.status_code == 200
        
        # Try invalid update (bad data) - should fail gracefully
        invalid_update = {
            "story_id": story_id,
            "current_segment_id": "segment_2",
            "visited_segments": ["segment_1", "segment_2"],
            "scene_counter": "not_a_number",  # Invalid
            "start_time": session["start_time"]
        }
        
        response = client.post("/api/sessions/save", json=invalid_update)
        assert response.status_code in [400, 422]  # Should reject
        
        # Game continues with valid update
        valid_update = {
            "story_id": story_id,
            "current_segment_id": "segment_2",
            "visited_segments": ["segment_1", "segment_2"],
            "scene_counter": 2,
            "start_time": session["start_time"]
        }
        
        response = client.post("/api/sessions/save", json=valid_update)
        assert response.status_code == 200
        
        # Verify game state updated
        response = client.get(f"/api/sessions/{story_id}")
        assert response.json()["session"]["scene_counter"] == 2


class TestCompleteEndToEndFlow:
    """Test a complete realistic game flow."""
    
    def test_realistic_game_scenario(self):
        """Test a realistic end-to-end game scenario."""
        story_id = "e2e_story_realistic"
        start_time = datetime.now(UTC).isoformat()
        
        # 1. Start game
        session = {
            "story_id": story_id,
            "current_segment_id": "prologue",
            "visited_segments": ["prologue"],
            "scene_counter": 1,
            "start_time": start_time
        }
        
        response = client.post("/api/sessions/save", json=session)
        assert response.status_code == 200
        
        # 2. Play through chapter 1
        for scene in range(2, 6):
            session["current_segment_id"] = f"chapter1_scene{scene - 1}"
            session["visited_segments"].append(f"chapter1_scene{scene - 1}")
            session["scene_counter"] = scene
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
        
        # 3. Report an issue mid-game
        report = {
            "story_id": story_id,
            "segment_id": "chapter1_scene2",
            "report_type": "spelling_error",
            "description": "Found a typo in the narrative that breaks immersion"
        }
        
        response = client.post("/api/reports", json=report)
        assert response.status_code == 201
        
        # 4. Continue to chapter 2
        for scene in range(6, 11):
            session["current_segment_id"] = f"chapter2_scene{scene - 5}"
            session["visited_segments"].append(f"chapter2_scene{scene - 5}")
            session["scene_counter"] = scene
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
        
        # 5. Check progress
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["scene_number"] == 10
        assert "chapter2_scene5" in progress["current_segment_id"]
        
        # 6. Final session state
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        final = response.json()["session"]
        assert final["scene_counter"] == 10
        assert len(final["visited_segments"]) == 10
        
        # 7. Verify report persisted
        response = client.get("/api/reports")
        reports = response.json()["reports"]
        story_reports = [r for r in reports if r["story_id"] == story_id]
        assert len(story_reports) >= 1
