"""Error handling and edge case tests for Phase 2.

Tests error scenarios, boundary conditions, and resilience.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, UTC
from pathlib import Path
import shutil
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Clean up test data after each test."""
    yield
    
    test_dir = Path(".infinite_story_data")
    if test_dir.exists():
        for story_dir in ["edge_case_*", "error_test_*", "boundary_*"]:
            for path in test_dir.glob(story_dir):
                if path.is_dir():
                    shutil.rmtree(path)


class TestSessionErrorHandling:
    """Test error handling in session endpoints."""
    
    def test_load_nonexistent_session_returns_not_found(self):
        """Loading non-existent session returns proper response."""
        response = client.get("/api/sessions/story_that_never_existed_xyz")
        assert response.status_code == 200
        assert response.json()["found"] is False
    
    def test_save_session_missing_story_id(self):
        """Session save without story_id is rejected."""
        invalid_session = {
            # Missing story_id
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_save_session_missing_current_segment(self):
        """Session save without current_segment_id is rejected."""
        invalid_session = {
            "story_id": "test_story",
            # Missing current_segment_id
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_save_session_invalid_scene_counter(self):
        """Session with negative scene_counter is rejected."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": -1,  # Invalid
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_save_session_scene_counter_zero(self):
        """Session with scene_counter of 0 is rejected."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 0,  # Invalid
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_delete_nonexistent_session_returns_404(self):
        """Deleting non-existent session returns 404."""
        response = client.delete("/api/sessions/nonexistent_story_xyz")
        assert response.status_code == 404
    
    def test_save_session_with_empty_visited_segments(self):
        """Session with empty visited_segments list might be invalid."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": [],  # Empty
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        # May accept or reject - implementation dependent
        assert response.status_code in [200, 400, 422]
    
    def test_save_session_current_not_in_visited(self):
        """Session where current_segment not in visited_segments."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_002",
            "visited_segments": ["segment_001"],  # Doesn't include current
            "scene_counter": 2,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        # May accept or reject - implementation dependent
        assert response.status_code in [200, 400, 422]


class TestProgressErrorHandling:
    """Test error handling in progress endpoints."""
    
    def test_get_progress_nonexistent_story(self):
        """Getting progress for non-existent story returns 404."""
        response = client.get("/api/progress/story_that_never_existed_xyz")
        assert response.status_code == 404
    
    def test_get_progress_invalid_story_id_format(self):
        """Getting progress with unusual story_id format."""
        # Special characters, spaces, etc
        response = client.get("/api/progress/story%20with%20spaces")
        # Should handle gracefully
        assert response.status_code in [200, 404]
    
    def test_get_progress_very_long_story_id(self):
        """Getting progress with very long story_id."""
        long_story_id = "a" * 1000
        response = client.get(f"/api/progress/{long_story_id}")
        # Should handle gracefully (may be 404, 414, or 500 depending on implementation)
        assert response.status_code in [404, 414, 500]


class TestReportErrorHandling:
    """Test error handling in report endpoints."""
    
    def test_submit_report_missing_story_id(self):
        """Report without story_id is rejected."""
        invalid_report = {
            # Missing story_id
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "This is a detailed report about the issue"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_submit_report_missing_segment_id(self):
        """Report without segment_id is rejected."""
        invalid_report = {
            "story_id": "test_story",
            # Missing segment_id
            "report_type": "inappropriate_content",
            "description": "This is a detailed report about the issue"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_submit_report_short_description(self):
        """Report with short description is rejected."""
        invalid_report = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Bad"  # Too short
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_submit_report_very_long_description(self):
        """Report with very long description is rejected."""
        invalid_report = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "a" * 3000  # Too long (max 2000)
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_submit_report_invalid_type(self):
        """Report with invalid report_type is rejected."""
        invalid_report = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "invalid_report_type_xyz",
            "description": "This is a detailed report about the issue"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_submit_report_missing_description(self):
        """Report without description is rejected."""
        invalid_report = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content"
            # Missing description
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_get_nonexistent_report(self):
        """Getting non-existent report returns 404."""
        response = client.get("/api/reports/report_that_never_existed_xyz")
        assert response.status_code == 404
    
    def test_delete_nonexistent_report(self):
        """Deleting non-existent report returns 404."""
        response = client.delete("/api/reports/report_that_never_existed_xyz")
        assert response.status_code == 404
    
    def test_list_reports_invalid_status_filter(self):
        """Listing reports with invalid status filter."""
        response = client.get("/api/reports?status=invalid_status_xyz")
        # Should either filter out or ignore
        assert response.status_code in [200, 400]
    
    def test_submit_report_invalid_email(self):
        """Report with invalid email format."""
        invalid_report = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "This is a detailed report about the issue",
            "reporter_email": "not_a_valid_email"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        # Email validation should reject
        assert response.status_code in [400, 422]


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_session_with_max_visited_segments(self):
        """Session with very large visited_segments list."""
        large_visited = [f"segment_{i:05d}" for i in range(1000)]
        
        session = {
            "story_id": "boundary_test",
            "current_segment_id": "segment_99999",
            "visited_segments": large_visited,
            "scene_counter": 1000,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session)
        # Should handle large list
        assert response.status_code in [200, 413]  # 413 = Payload too large
    
    def test_session_with_special_characters_in_ids(self):
        """Session with special characters in segment IDs."""
        session = {
            "story_id": "boundary_test",
            "current_segment_id": "segment@#$%&",
            "visited_segments": ["segment@#$%&"],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session)
        # Should handle or reject gracefully
        assert response.status_code in [200, 400, 422]
    
    def test_report_with_unicode_characters(self):
        """Report with unicode characters in description."""
        report = {
            "story_id": "boundary_test",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Unicode test: 你好世界 мир 🌍 العالم"
        }
        
        response = client.post("/api/reports", json=report)
        # Should handle unicode
        assert response.status_code in [200, 201, 400, 422]
    
    def test_progress_with_very_high_scene_counter(self):
        """Progress for session with very high scene number."""
        session = {
            "story_id": "boundary_progress",
            "current_segment_id": "segment_999999",
            "visited_segments": [f"segment_{i}" for i in range(99999, 100000)],
            "scene_counter": 999999,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        client.post("/api/sessions/save", json=session)
        
        response = client.get("/api/progress/boundary_progress")
        # Should handle large numbers
        if response.status_code == 200:
            assert "scene_number" in response.json()


class TestConcurrencyEdgeCases:
    """Test concurrent access edge cases."""
    
    def test_session_update_race_condition(self):
        """Test rapid consecutive session updates."""
        story_id = "concurrency_test"
        
        # Simulate rapid updates
        for i in range(5):
            session = {
                "story_id": story_id,
                "current_segment_id": f"segment_{i:03d}",
                "visited_segments": [f"segment_{j:03d}" for j in range(i + 1)],
                "scene_counter": i + 1,
                "start_time": datetime.now(UTC).isoformat()
            }
            
            response = client.post("/api/sessions/save", json=session)
            assert response.status_code == 200
        
        # Final state should be consistent
        response = client.get(f"/api/sessions/{story_id}")
        assert response.status_code == 200
        final = response.json()["session"]
        # Should have latest state
        assert final["scene_counter"] == 5
    
    def test_report_submission_race_condition(self):
        """Test rapid consecutive report submissions."""
        story_id = "report_race_test"
        
        report_ids = []
        for i in range(3):
            report = {
                "story_id": story_id,
                "segment_id": f"segment_{i:03d}",
                "report_type": "inappropriate_content",
                "description": f"Report number {i} with detailed description"
            }
            
            response = client.post("/api/reports", json=report)
            assert response.status_code == 201
            report_ids.append(response.json()["report_id"])
        
        # All reports should be stored independently
        assert len(report_ids) == len(set(report_ids))  # All unique


class TestDataValidation:
    """Test data validation and type checking."""
    
    def test_session_string_scene_counter(self):
        """Session with string scene_counter instead of int."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": "not_a_number",
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_session_invalid_datetime(self):
        """Session with invalid datetime format."""
        invalid_session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
            "scene_counter": 1,
            "start_time": "not_a_valid_datetime"
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_report_null_fields(self):
        """Report with null required fields."""
        invalid_report = {
            "story_id": None,
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Detailed description of the issue"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]


class TestEmptyAndNullResponses:
    """Test handling of empty and null data."""
    
    def test_list_reports_empty_result(self):
        """Listing reports when none exist."""
        response = client.get("/api/reports?story_id=story_that_has_no_reports_xyz")
        assert response.status_code == 200
        # Should return empty list, not error
        reports = response.json().get("reports", [])
        assert isinstance(reports, list)
    
    def test_session_with_no_segments_visited(self):
        """Attempting to save session with no visited segments might be edge case."""
        session = {
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": [],
            "scene_counter": 1,
            "start_time": datetime.now(UTC).isoformat()
        }
        
        response = client.post("/api/sessions/save", json=session)
        # Implementation dependent - may accept or reject
        assert response.status_code in [200, 400, 422]
