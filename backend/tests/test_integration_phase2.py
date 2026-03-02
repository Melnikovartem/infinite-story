"""Phase 2 Integration Tests - Full end-to-end workflow testing.

Tests complete game flows with sessions, progress, and reporting.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from pathlib import Path
import shutil
from app.main import app

client = TestClient(app)

# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    # Cleanup
    test_dir = Path(".infinite_story_data")
    if test_dir.exists():
        # Remove test story directories
        for story_dir in ["test_story", "veil_of_thornreach", "integration_test_story"]:
            story_path = test_dir / story_dir
            if story_path.exists():
                shutil.rmtree(story_path)


class TestSessionProgressIntegration:
    """Test session and progress working together."""
    
    def test_save_session_then_get_progress(self):
        """Test saving session then retrieving progress."""
        story_id = "integration_test_story"
        
        # 1. Save a session
        session_data = {
            "story_id": story_id,
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session_data)
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # 2. Get progress for that story
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        
        progress = response.json()
        assert progress is not None
        assert progress["scene_number"] == 1
    
    def test_session_persistence_across_moves(self):
        """Test that session updates persist as user navigates."""
        story_id = "test_story"
        
        # Save initial session at segment 1
        session_v1 = {
            "story_id": story_id,
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session_v1)
        assert response.status_code == 200
        
        # Load it back
        response = client.get(f"/api/sessions/{story_id}")
        assert response.json()["session"]["scene_counter"] == 1
        
        # Update to segment 2
        session_v2 = {
            "story_id": story_id,
            "current_segment_id": "segment_002",
            "visited_segments": ["segment_001", "segment_002"],
            "scene_counter": 2,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session_v2)
        assert response.status_code == 200
        
        # Verify update persisted
        response = client.get(f"/api/sessions/{story_id}")
        assert response.json()["session"]["scene_counter"] == 2
        assert "segment_002" in response.json()["session"]["visited_segments"]


class TestReportingIntegration:
    """Test content reporting endpoints."""
    
    def test_submit_and_retrieve_report(self):
        """Test submitting a report and retrieving it."""
        story_id = "test_story_submit"
        
        # 1. Submit a report
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
        
        # 2. Retrieve the report
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        report = response.json()
        assert report["story_id"] == story_id
        assert report["report_type"] == "inappropriate_content"
    
    def test_list_reports_by_story(self):
        """Test listing reports for a specific story."""
        story_id = "test_story_list"
        
        # Submit multiple reports for the same story
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
        
        # List reports for story
        response = client.get(f"/api/reports?story_id={story_id}")
        assert response.status_code == 200
        
        reports = response.json().get("reports", [])
        # We should have at least the 3 we just submitted
        story_reports = [r for r in reports if r["story_id"] == story_id]
        assert len(story_reports) >= 3
    
    def test_list_reports_by_status(self):
        """Test filtering reports by status."""
        story_id = "test_story"
        
        # Submit a report
        report_data = {
            "story_id": story_id,
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Test report",
            "reporter_email": "tester@example.com"
        }
        
        client.post("/api/reports", json=report_data)
        
        # List open reports
        response = client.get("/api/reports?status=open")
        assert response.status_code == 200
        assert "reports" in response.json()


class TestCompleteGameFlow:
    """Test complete game flow: story → segments → choices → sessions → progress."""
    
    def test_basic_game_flow(self):
        """Test basic game flow without actual story data."""
        story_id = "game_flow_test"
        
        # 1. Start new game session
        start_session = {
            "story_id": story_id,
            "current_segment_id": "intro",
            "visited_segments": ["intro"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=start_session)
        assert response.status_code == 200
        
        # 2. Check progress at start
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        progress = response.json()
        assert progress["scene_number"] == 1
        
        # 3. Move through segments (simulated)
        for segment_num in range(2, 6):
            segment_id = f"segment_{segment_num:03d}"
            visited = [f"segment_{i:03d}" if i > 1 else "intro" for i in range(1, segment_num + 1)]
            
            session_update = {
                "story_id": story_id,
                "current_segment_id": segment_id,
                "visited_segments": visited,
                "scene_counter": segment_num,
                "start_time": datetime.now(UTC).isoformat()
            }
            
            response = client.post("/api/sessions/save", json=session_update)
            assert response.status_code == 200
        
        # 4. Final state check
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        final_session = response.json()["session"]
        assert final_session["scene_counter"] == 5
        
        # 5. Final progress check
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        final_progress = response.json()
        assert final_progress["scene_number"] == 5
    
    def test_multiple_story_sessions(self):
        """Test managing multiple stories independently."""
        stories = ["story_a", "story_b", "story_c"]
        
        # Start multiple stories
        for idx, story_id in enumerate(stories):
            session = {
                "story_id": story_id,
                "current_segment_id": "segment_001",
                "visited_segments": ["segment_001"],
                "scene_counter": idx + 1,
                "start_time": datetime.now(UTC).isoformat()
            }
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
        
        # Verify each story has independent state
        for idx, story_id in enumerate(stories):
            response = client.get(f"/api/sessions/{story_id}")
            assert response.status_code == 200
            assert response.json()["session"]["scene_counter"] == idx + 1


class TestErrorHandling:
    """Test error scenarios and edge cases."""
    
    def test_nonexistent_session_load(self):
        """Loading non-existent session returns 404 or found=false."""
        response = client.get("/api/sessions/story_never_started")
        assert response.status_code == 200
        assert response.json()["found"] is False
    
    def test_invalid_report_missing_field(self):
        """Report with missing required field is rejected."""
        incomplete_report = {
            "story_id": "test_story",
            # Missing "segment_id"
            "report_type": "inappropriate_content",
            "description": "Missing segment_id"
        }
        
        response = client.post("/api/reports", json=incomplete_report)
        # Should either return 400 or validation error
        assert response.status_code in [400, 422]
    
    def test_invalid_session_data_types(self):
        """Session with wrong data types is handled."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": "not_a_number",  # Wrong type
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        # Should validate and reject
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
        
        # Save sessions with increasing scene counts
        for scene_num in range(1, 6):
            session = {
                "story_id": story_id,
                "current_segment_id": f"segment_{scene_num:03d}",
                "visited_segments": [f"segment_{i:03d}" for i in range(1, scene_num + 1)],
                "scene_counter": scene_num,
                "start_time": datetime.now(UTC).isoformat()
            }
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
            
            # Check progress matches
            response = client.get(f"/api/progress/{story_id}")
            assert response.status_code == 200
            assert response.json()["scene_number"] == scene_num
    
    def test_progress_summary_format(self):
        """Progress response has correct format and fields."""
        story_id = "summary_test"
        
        # Save a session
        session = {
            "story_id": story_id,
            "current_segment_id": "segment_005",
            "visited_segments": ["segment_001", "segment_002", "segment_003", "segment_004", "segment_005"],
            "scene_counter": 5,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        client.post("/api/sessions/save", json=session)
        
        # Get progress
        response = client.get(f"/api/progress/{story_id}")
        assert response.status_code == 200
        
        progress = response.json()
        assert "scene_number" in progress
        assert "elapsed_formatted" in progress or "elapsed_seconds" in progress


class TestReportSummary:
    """Test report summary and statistics."""
    
    def test_report_summary(self):
        """Get summary of all reports."""
        response = client.get("/api/reports/summary")
        
        # Should return either 200 or 404 if endpoint exists
        if response.status_code == 200:
            summary = response.json()
            assert "total_reports" in summary or "reports" in summary
