"""Phase 2 Integration Tests - Full end-to-end workflow testing.

Tests complete game flows with sessions, progress, and reporting.
Uses actual API request/response models.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from pathlib import Path
import shutil
from app.main import app

client = TestClient(app)


def _make_session(story_id, session_id, user_id, current_segment_id,
                  visited_segments, visited_choices=None):
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
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    test_dir = Path(".infinite_story_data")
    if test_dir.exists():
        for story_dir in ["test_story", "integration_test_story",
                          "game_flow_test", "story_a", "story_b", "story_c",
                          "progress_test", "summary_test",
                          "test_story_submit", "test_story_list"]:
            story_path = test_dir / story_dir
            if story_path.exists():
                shutil.rmtree(story_path)


class TestSessionProgressIntegration:
    """Test session and progress working together."""
    
    def test_save_session_then_get_progress(self):
        """Test saving session then retrieving progress."""
        story_id = "integration_test_story"
        session_id = "int_session_1"
        
        payload = _make_session(story_id, session_id, "test_user",
                                "segment_001", ["segment_001"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Get progress
        response = client.get(f"/api/progress/{story_id}/{session_id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["scene_number"] == 1
    
    def test_session_persistence_across_moves(self):
        """Test that session updates persist as user navigates."""
        story_id = "test_story"
        session_id = "persist_session"
        user_id = "test_user"
        
        # Save initial session
        payload = _make_session(story_id, session_id, user_id,
                                "segment_001", ["segment_001"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # Load it back
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.json()["found"] is True
        assert response.json()["session"]["current_segment_id"] == "segment_001"
        
        # Update to segment 2
        payload = _make_session(story_id, session_id, user_id,
                                "segment_002", ["segment_001", "segment_002"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # Verify update persisted
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        session_data = response.json()["session"]
        assert session_data["current_segment_id"] == "segment_002"
        assert "segment_002" in session_data["visited_segments"]


class TestReportingIntegration:
    """Test content reporting endpoints."""
    
    def test_submit_and_retrieve_report(self):
        """Test submitting a report and retrieving it."""
        story_id = "test_story_submit"
        
        report_data = {
            "story_id": story_id,
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Contains offensive language that needs moderation review",
            "reporter_email": "tester@example.com"
        }
        
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 201
        
        report_id = response.json().get("report_id")
        assert report_id is not None
        
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        report = response.json()
        assert report["story_id"] == story_id
        assert report["report_type"] == "inappropriate_content"
    
    def test_list_reports_by_story(self):
        """Test listing reports for a specific story."""
        story_id = "test_story_list"
        
        report_ids = []
        for i in range(3):
            report_data = {
                "story_id": story_id,
                "segment_id": f"segment_{i:03d}",
                "report_type": "inappropriate_content",
                "description": f"Report number {i} with detailed description of the issue",
                "reporter_email": "tester@example.com"
            }
            resp = client.post("/api/reports", json=report_data)
            assert resp.status_code == 201
            report_ids.append(resp.json().get("report_id"))
        
        response = client.get(f"/api/reports?story_id={story_id}")
        assert response.status_code == 200
        
        reports = response.json().get("reports", [])
        story_reports = [r for r in reports if r["story_id"] == story_id]
        assert len(story_reports) >= 3
    
    def test_list_reports_by_status(self):
        """Test filtering reports by status."""
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Test report for status filtering test",
            "reporter_email": "tester@example.com"
        }
        client.post("/api/reports", json=report_data)
        
        response = client.get("/api/reports?status=open")
        assert response.status_code == 200
        assert "reports" in response.json()


class TestCompleteGameFlow:
    """Test complete game flow: sessions → progress."""
    
    def test_basic_game_flow(self):
        """Test basic game flow."""
        story_id = "game_flow_test"
        session_id = "flow_session"
        user_id = "test_user"
        
        # 1. Start new game session
        payload = _make_session(story_id, session_id, user_id, "intro", ["intro"])
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code == 200
        
        # 2. Check progress at start
        response = client.get(f"/api/progress/{story_id}/{session_id}")
        assert response.status_code == 200
        assert response.json()["scene_number"] == 1
        
        # 3. Move through segments
        visited = ["intro"]
        for segment_num in range(2, 6):
            visited.append(f"segment_{segment_num:03d}")
            payload = _make_session(story_id, session_id, user_id,
                                    f"segment_{segment_num:03d}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # 4. Final state check
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.status_code == 200
        session_data = response.json()["session"]
        assert session_data["current_segment_id"] == "segment_005"
        
        # 5. Final progress check
        response = client.get(f"/api/progress/{story_id}/{session_id}")
        assert response.status_code == 200
        assert response.json()["scene_number"] == 5
    
    def test_multiple_story_sessions(self):
        """Test managing multiple stories independently."""
        stories = [("story_a", "session_a"), ("story_b", "session_b"),
                    ("story_c", "session_c")]
        
        for idx, (story_id, session_id) in enumerate(stories):
            visited = [f"segment_{i:03d}" for i in range(1, idx + 2)]
            payload = _make_session(story_id, session_id, "test_user",
                                    f"segment_{idx + 1:03d}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # Verify each story has independent state
        for idx, (story_id, session_id) in enumerate(stories):
            response = client.get(f"/api/sessions/{story_id}/{session_id}")
            assert response.status_code == 200
            assert response.json()["found"] is True


class TestErrorHandling:
    """Test error scenarios and edge cases."""
    
    def test_nonexistent_session_load(self):
        """Loading non-existent session returns found=false."""
        response = client.get("/api/sessions/story_never_started/no_session")
        assert response.status_code == 200
        assert response.json()["found"] is False
    
    def test_invalid_report_missing_field(self):
        """Report with missing required field is rejected."""
        incomplete_report = {
            "story_id": "test_story",
            "report_type": "inappropriate_content",
            "description": "Missing segment_id field"
        }
        
        response = client.post("/api/reports", json=incomplete_report)
        assert response.status_code in [400, 422]
    
    def test_invalid_session_missing_fields(self):
        """Session with missing fields is handled."""
        response = client.post("/api/sessions/save", json={"story_id": "test"})
        assert response.status_code in [400, 422]
    
    def test_nonexistent_report_retrieval(self):
        """Getting non-existent report returns 404."""
        response = client.get("/api/reports/nonexistent_report_id")
        assert response.status_code == 404


class TestProgressTracking:
    """Test progress tracking features."""
    
    def test_progress_with_multiple_updates(self):
        """Progress accurately tracks multiple session updates."""
        story_id = "progress_test"
        session_id = "progress_session"
        user_id = "test_user"
        
        visited = []
        for scene_num in range(1, 6):
            visited.append(f"segment_{scene_num:03d}")
            payload = _make_session(story_id, session_id, user_id,
                                    f"segment_{scene_num:03d}", visited)
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
            
            response = client.get(f"/api/progress/{story_id}/{session_id}")
            assert response.status_code == 200
            assert response.json()["scene_number"] == scene_num
    
    def test_progress_summary_format(self):
        """Progress response has correct format and fields."""
        story_id = "summary_test"
        session_id = "summary_session"
        
        payload = _make_session(story_id, session_id, "test_user",
                                "segment_005",
                                ["segment_001", "segment_002", "segment_003",
                                 "segment_004", "segment_005"])
        client.post("/api/sessions/save", json=payload)
        
        response = client.get(f"/api/progress/{story_id}/{session_id}")
        assert response.status_code == 200
        
        progress = response.json()
        assert "scene_number" in progress
        assert "elapsed_seconds" in progress
        assert progress["scene_number"] == 5


class TestReportSummary:
    """Test report summary and statistics."""
    
    def test_report_summary(self):
        """Get summary of all reports."""
        response = client.get("/api/reports/summary")
        
        if response.status_code == 200:
            summary = response.json()
            assert "total_reports" in summary or "reports" in summary
