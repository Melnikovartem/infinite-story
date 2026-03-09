"""Error handling and edge case tests for Phase 2.

Tests error scenarios, boundary conditions, and resilience.
Uses the actual API request/response models.
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
        for story_dir in ["edge_case_*", "error_test_*", "boundary_*",
                          "concurrency_*", "test_story"]:
            for path in test_dir.glob(story_dir):
                if path.is_dir():
                    shutil.rmtree(path)


class TestSessionErrorHandling:
    """Test error handling in session endpoints."""
    
    def test_load_nonexistent_session_returns_not_found(self):
        """Loading non-existent session returns proper response."""
        response = client.get("/api/sessions/story_xyz/session_xyz")
        assert response.status_code == 200
        assert response.json()["found"] is False
    
    def test_save_session_missing_story_id(self):
        """Session save without story_id is rejected."""
        invalid_session = {
            "id": "test_session",
            "user_id": "test_user",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_save_session_missing_current_segment(self):
        """Session save without current_segment_id is rejected."""
        invalid_session = {
            "id": "test_session",
            "story_id": "test_story",
            "user_id": "test_user",
            "visited_segments": ["segment_001"],
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_save_session_missing_user_id(self):
        """Session save without user_id is rejected."""
        invalid_session = {
            "id": "test_session",
            "story_id": "test_story",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_save_session_missing_id(self):
        """Session save without id is rejected."""
        invalid_session = {
            "story_id": "test_story",
            "user_id": "test_user",
            "current_segment_id": "segment_001",
            "visited_segments": ["segment_001"],
        }
        
        response = client.post("/api/sessions/save", json=invalid_session)
        assert response.status_code in [400, 422]
    
    def test_delete_nonexistent_session_returns_404(self):
        """Deleting non-existent session returns 404."""
        response = client.delete("/api/sessions/nonexistent_story_xyz/nonexistent_session")
        assert response.status_code == 404
    
    def test_save_session_with_empty_visited_segments(self):
        """Session with empty visited_segments list."""
        payload = _make_session("test_story", "empty_session", "test_user",
                                "segment_001", [])
        response = client.post("/api/sessions/save", json=payload)
        # SessionState.__init__ auto-adds current_segment_id to visited
        assert response.status_code in [200, 400, 422]
    
    def test_save_session_current_not_in_visited(self):
        """Session where current_segment not in visited_segments."""
        payload = _make_session("test_story", "mismatch_session", "test_user",
                                "segment_002", ["segment_001"])
        response = client.post("/api/sessions/save", json=payload)
        # SessionState.__init__ auto-adds current to visited
        assert response.status_code in [200, 400, 422]


class TestProgressErrorHandling:
    """Test error handling in progress endpoints."""
    
    def test_get_progress_nonexistent_story(self):
        """Getting progress for non-existent story returns 404."""
        response = client.get("/api/progress/story_xyz/session_xyz")
        assert response.status_code == 404
    
    def test_get_progress_invalid_story_id_format(self):
        """Getting progress with unusual story_id format."""
        response = client.get("/api/progress/story%20with%20spaces/session_1")
        assert response.status_code in [200, 404]
    
    def test_get_progress_very_long_story_id(self):
        """Getting progress with very long story_id."""
        long_id = "a" * 1000
        response = client.get(f"/api/progress/{long_id}/session_1")
        assert response.status_code in [404, 414, 500]


class TestReportErrorHandling:
    """Test error handling in report endpoints."""
    
    def test_submit_report_missing_story_id(self):
        """Report without story_id is rejected."""
        invalid_report = {
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
            "description": "Bad"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]
    
    def test_submit_report_very_long_description(self):
        """Report with very long description is rejected."""
        invalid_report = {
            "story_id": "test_story",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "a" * 3000
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
        assert response.status_code in [400, 422]


class TestBoundaryConditions:
    """Test boundary conditions and edge cases."""
    
    def test_session_with_max_visited_segments(self):
        """Session with very large visited_segments list."""
        large_visited = [f"segment_{i:05d}" for i in range(1000)]
        payload = _make_session("boundary_test", "large_session", "test_user",
                                "segment_00999", large_visited)
        
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code in [200, 413]
    
    def test_session_with_special_characters_in_ids(self):
        """Session with special characters in segment IDs."""
        payload = _make_session("boundary_test", "special_session", "test_user",
                                "segment@special", ["segment@special"])
        
        response = client.post("/api/sessions/save", json=payload)
        assert response.status_code in [200, 400, 422]
    
    def test_report_with_unicode_characters(self):
        """Report with unicode characters in description."""
        report = {
            "story_id": "boundary_test",
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Unicode test: 你好世界 мир العالم - more text to meet length"
        }
        
        response = client.post("/api/reports", json=report)
        assert response.status_code in [200, 201, 400, 422]


class TestConcurrencyEdgeCases:
    """Test concurrent access edge cases."""
    
    def test_session_update_race_condition(self):
        """Test rapid consecutive session updates."""
        story_id = "concurrency_test"
        session_id = "race_session"
        user_id = "test_user"
        
        # Simulate rapid updates
        visited = []
        for i in range(5):
            visited.append(f"segment_{i:03d}")
            payload = _make_session(story_id, session_id, user_id,
                                    f"segment_{i:03d}", visited.copy())
            response = client.post("/api/sessions/save", json=payload)
            assert response.status_code == 200
        
        # Final state should be consistent
        response = client.get(f"/api/sessions/{story_id}/{session_id}")
        assert response.status_code == 200
        final = response.json()["session"]
        assert final["current_segment_id"] == "segment_004"
    
    def test_report_submission_race_condition(self):
        """Test rapid consecutive report submissions."""
        story_id = "report_race_test"
        
        report_ids = []
        for i in range(3):
            report = {
                "story_id": story_id,
                "segment_id": f"segment_{i:03d}",
                "report_type": "inappropriate_content",
                "description": f"Report number {i} with detailed description of the issue"
            }
            
            response = client.post("/api/reports", json=report)
            assert response.status_code == 201
            report_ids.append(response.json()["report_id"])
        
        assert len(report_ids) == len(set(report_ids))


class TestDataValidation:
    """Test data validation and type checking."""
    
    def test_session_completely_empty_body(self):
        """Session with empty JSON body."""
        response = client.post("/api/sessions/save", json={})
        assert response.status_code in [400, 422]
    
    def test_report_null_fields(self):
        """Report with null required fields."""
        invalid_report = {
            "story_id": None,
            "segment_id": "segment_001",
            "report_type": "inappropriate_content",
            "description": "Detailed description of the issue found here"
        }
        
        response = client.post("/api/reports", json=invalid_report)
        assert response.status_code in [400, 422]


class TestEmptyAndNullResponses:
    """Test handling of empty and null data."""
    
    def test_list_reports_empty_result(self):
        """Listing reports when none exist for a story."""
        response = client.get("/api/reports?story_id=story_that_has_no_reports_xyz")
        assert response.status_code == 200
        reports = response.json().get("reports", [])
        assert isinstance(reports, list)
