"""Tests for content reporting API endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app
from app.utils.content_report import ContentReport

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_reports():
    """Clean up test reports."""
    yield
    # Cleanup after test
    reports_dir = Path(".infinite_story_data") / "reports"
    if reports_dir.exists():
        for f in reports_dir.glob("*.json"):
            f.unlink()


class TestReportEndpoints:
    """Test content reporting endpoints."""
    
    def test_submit_report(self):
        """Test submitting a content report."""
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "inappropriate_content",
            "description": "This segment contains offensive language that needs review"
        }
        
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 201
        assert response.json()["success"] is True
        assert "report_id" in response.json()
    
    def test_submit_report_with_email(self):
        """Test submitting a report with email."""
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "bug",
            "description": "This segment has a broken narrative" * 2,
            "reporter_email": "user@example.com"
        }
        
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 201
        assert response.json()["success"] is True
    
    def test_submit_report_invalid_type(self):
        """Test submitting report with invalid type."""
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "invalid_type",
            "description": "This is a test" * 3
        }
        
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 400
    
    def test_submit_report_short_description(self):
        """Test submitting report with too short description."""
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "other",
            "description": "short"
        }
        
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 422  # Validation error
    
    def test_list_all_reports(self):
        """Test listing all reports."""
        # Submit a few reports
        for i in range(3):
            report_data = {
                "story_id": f"story_{i}",
                "segment_id": f"segment_{i}",
                "report_type": "bug" if i % 2 == 0 else "other",
                "description": "Test report number " * 3
            }
            client.post("/api/reports", json=report_data)
        
        # List all
        response = client.get("/api/reports")
        assert response.status_code == 200
        assert response.json()["total"] >= 3
    
    def test_list_reports_by_story(self):
        """Test filtering reports by story."""
        # Submit reports for different stories
        for i in range(2):
            report_data = {
                "story_id": "story_a",
                "segment_id": f"segment_{i}",
                "report_type": "bug",
                "description": "Test report for story A" * 2
            }
            client.post("/api/reports", json=report_data)
        
        report_data = {
            "story_id": "story_b",
            "segment_id": "segment_0",
            "report_type": "other",
            "description": "Test report for story B" * 2
        }
        client.post("/api/reports", json=report_data)
        
        # Filter by story_a
        response = client.get("/api/reports?story_id=story_a")
        assert response.status_code == 200
        assert response.json()["total"] == 2
        assert all(r["story_id"] == "story_a" for r in response.json()["reports"])
    
    def test_list_reports_by_status(self):
        """Test filtering reports by status."""
        # Submit a report
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "bug",
            "description": "Test report status filtering" * 2
        }
        
        response = client.post("/api/reports", json=report_data)
        assert response.status_code == 201
        
        # Filter by status
        response = client.get("/api/reports?status_filter=new")
        assert response.status_code == 200
        assert response.json()["total"] >= 1
    
    def test_get_report(self):
        """Test getting a specific report."""
        # Submit a report
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "inappropriate_content",
            "description": "Test getting specific report" * 2
        }
        
        response = client.post("/api/reports", json=report_data)
        report_id = response.json()["report_id"]
        
        # Get it
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 200
        assert response.json()["id"] == report_id
        assert response.json()["story_id"] == "test_story"
    
    def test_get_nonexistent_report(self):
        """Test getting a report that doesn't exist."""
        response = client.get("/api/reports/nonexistent_id")
        assert response.status_code == 404
    
    def test_delete_report(self):
        """Test deleting a report."""
        # Submit a report
        report_data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "report_type": "bug",
            "description": "Test deleting report" * 2
        }
        
        response = client.post("/api/reports", json=report_data)
        report_id = response.json()["report_id"]
        
        # Delete it
        response = client.delete(f"/api/reports/{report_id}")
        assert response.status_code == 200
        
        # Verify it's gone
        response = client.get(f"/api/reports/{report_id}")
        assert response.status_code == 404
    
    def test_get_report_summary(self):
        """Test getting report summary statistics."""
        # Submit various reports
        for i in range(3):
            report_data = {
                "story_id": f"story_{i}",
                "segment_id": f"segment_{i}",
                "report_type": "bug" if i % 2 == 0 else "inappropriate_content",
                "description": "Test for summary" * 3
            }
            client.post("/api/reports", json=report_data)
        
        response = client.get("/api/reports/summary/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_reports"] >= 3
        assert data["new_reports"] >= 3
        assert "by_type" in data
