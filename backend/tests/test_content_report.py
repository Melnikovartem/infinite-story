"""Tests for content reporting system."""

import pytest
from pathlib import Path
import json
from app.utils.content_report import ContentReport, ReportType, ReportStatus


class TestContentReportModel:
    """Test ContentReport model creation and validation."""
    
    def test_creation(self):
        """Test creating a content report."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This segment contains offensive language that should be reviewed",
            report_type=ReportType.INAPPROPRIATE_CONTENT
        )
        
        assert report.story_id == "test_story"
        assert report.segment_id == "segment_1"
        assert report.report_type == ReportType.INAPPROPRIATE_CONTENT
        assert report.status == ReportStatus.NEW
        assert len(report.id) > 0
    
    def test_report_requires_description(self):
        """Test that report requires minimum length description."""
        with pytest.raises(ValueError):
            ContentReport(
                story_id="test_story",
                segment_id="segment_1",
                description="short"  # Too short
            )
    
    def test_description_max_length(self):
        """Test that description has maximum length."""
        long_desc = "a" * 2001
        with pytest.raises(ValueError):
            ContentReport(
                story_id="test_story",
                segment_id="segment_1",
                description=long_desc
            )
    
    def test_report_with_email(self):
        """Test creating report with email."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This segment has a problem that needs review",
            reporter_email="user@example.com"
        )
        
        assert report.reporter_email == "user@example.com"
    
    def test_report_with_invalid_email(self):
        """Test that invalid email is rejected."""
        with pytest.raises(ValueError):
            ContentReport(
                story_id="test_story",
                segment_id="segment_1",
                description="This segment has a problem",
                reporter_email="not-an-email"
            )
    
    def test_mark_reviewed(self):
        """Test marking report as reviewed."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This segment needs review"
        )
        
        assert report.status == ReportStatus.NEW
        report.mark_reviewed("No issues found")
        assert report.status == ReportStatus.REVIEWED
        assert report.reviewer_notes == "No issues found"
        assert report.reviewed_at is not None
    
    def test_resolve(self):
        """Test resolving a report."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This segment has offensive content"
        )
        
        report.resolve("Content has been updated")
        assert report.status == ReportStatus.RESOLVED
        assert report.reviewer_notes == "Content has been updated"
    
    def test_dismiss(self):
        """Test dismissing a report."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This segment is problematic"
        )
        
        report.dismiss("False report")
        assert report.status == ReportStatus.DISMISSED
        assert report.reviewer_notes == "False report"


class TestContentReportSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self):
        """Test converting report to dictionary."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This needs review" * 3,
            report_type=ReportType.BUG
        )
        
        data = report.to_dict()
        assert isinstance(data, dict)
        assert data["story_id"] == "test_story"
        assert data["report_type"] == "bug"
    
    def test_from_dict(self):
        """Test creating report from dictionary."""
        data = {
            "story_id": "test_story",
            "segment_id": "segment_1",
            "description": "This segment has a problem" * 2,
            "report_type": "inappropriate_content",
            "status": "new"
        }
        
        report = ContentReport.from_dict(data)
        assert report.story_id == "test_story"
        assert report.report_type == ReportType.INAPPROPRIATE_CONTENT


class TestContentReportFileIO:
    """Test file operations."""
    
    def setup_method(self):
        """Clean up test reports."""
        reports_dir = Path(".infinite_story_data") / "reports"
        if reports_dir.exists():
            for f in reports_dir.glob("*.json"):
                f.unlink()
    
    def teardown_method(self):
        """Clean up after tests."""
        reports_dir = Path(".infinite_story_data") / "reports"
        if reports_dir.exists():
            for f in reports_dir.glob("*.json"):
                f.unlink()
    
    def test_save_to_file(self):
        """Test saving report to file."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This segment needs review" * 2
        )
        
        file_path = ContentReport.save_to_file(report)
        assert file_path.exists()
        assert file_path.name.endswith(".json")
    
    def test_load_from_file(self):
        """Test loading report from file."""
        # Save first
        report_original = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="This is a test report" * 2,
            report_type=ReportType.BUG
        )
        report_id = report_original.id
        ContentReport.save_to_file(report_original)
        
        # Load
        report_loaded = ContentReport.load_from_file(report_id)
        assert report_loaded is not None
        assert report_loaded.story_id == "test_story"
        assert report_loaded.report_type == ReportType.BUG
    
    def test_load_nonexistent(self):
        """Test loading nonexistent report."""
        report = ContentReport.load_from_file("nonexistent_id")
        assert report is None
    
    def test_delete_from_file(self):
        """Test deleting report from file."""
        report = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="Report to delete" * 2
        )
        report_id = report.id
        ContentReport.save_to_file(report)
        
        # Verify exists
        assert ContentReport.load_from_file(report_id) is not None
        
        # Delete
        deleted = ContentReport.delete_from_file(report_id)
        assert deleted is True
        assert ContentReport.load_from_file(report_id) is None
    
    def test_list_all(self):
        """Test listing all reports."""
        # Save a few reports
        for i in range(3):
            report = ContentReport(
                story_id=f"story_{i}",
                segment_id=f"segment_{i}",
                description="Test report number " * 3
            )
            ContentReport.save_to_file(report)
        
        reports = ContentReport.list_all()
        assert len(reports) >= 3
    
    def test_list_by_story(self):
        """Test listing reports by story."""
        # Save reports for different stories
        for i in range(2):
            report = ContentReport(
                story_id="story_a",
                segment_id=f"segment_{i}",
                description="Test report for story A" * 2
            )
            ContentReport.save_to_file(report)
        
        report_b = ContentReport(
            story_id="story_b",
            segment_id="segment_0",
            description="Test report for story B" * 2
        )
        ContentReport.save_to_file(report_b)
        
        # List by story
        reports_a = ContentReport.list_by_story("story_a")
        reports_b = ContentReport.list_by_story("story_b")
        
        assert len(reports_a) >= 2
        assert len(reports_b) >= 1
        assert all(r.story_id == "story_a" for r in reports_a)
        assert all(r.story_id == "story_b" for r in reports_b)
    
    def test_list_by_status(self):
        """Test listing reports by status."""
        # Create and save reports
        report1 = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="Report one for testing" * 2
        )
        report1_id = report1.id
        ContentReport.save_to_file(report1)
        
        report2 = ContentReport(
            story_id="test_story",
            segment_id="segment_2",
            description="Report two for testing" * 2
        )
        ContentReport.save_to_file(report2)
        
        # Mark one as reviewed
        report1_loaded = ContentReport.load_from_file(report1_id)
        report1_loaded.mark_reviewed()
        ContentReport.save_to_file(report1_loaded)
        
        # List by status
        new_reports = ContentReport.list_by_status(ReportStatus.NEW)
        reviewed_reports = ContentReport.list_by_status(ReportStatus.REVIEWED)
        
        assert len(new_reports) >= 1
        assert len(reviewed_reports) >= 1
    
    def test_list_by_type(self):
        """Test listing reports by type."""
        # Create reports of different types
        report1 = ContentReport(
            story_id="test_story",
            segment_id="segment_1",
            description="Inappropriate content report" * 2,
            report_type=ReportType.INAPPROPRIATE_CONTENT
        )
        ContentReport.save_to_file(report1)
        
        report2 = ContentReport(
            story_id="test_story",
            segment_id="segment_2",
            description="Bug report" * 3,
            report_type=ReportType.BUG
        )
        ContentReport.save_to_file(report2)
        
        # List by type
        inapp_reports = ContentReport.list_by_type(ReportType.INAPPROPRIATE_CONTENT)
        bug_reports = ContentReport.list_by_type(ReportType.BUG)
        
        assert len(inapp_reports) >= 1
        assert len(bug_reports) >= 1
    
    def test_get_report_summary(self):
        """Test getting report summary."""
        # Create various reports
        for i in range(3):
            report = ContentReport(
                story_id=f"story_{i}",
                segment_id=f"segment_{i}",
                description="Test report for summary" * 2,
                report_type=ReportType.BUG if i % 2 == 0 else ReportType.OTHER
            )
            ContentReport.save_to_file(report)
        
        summary = ContentReport.get_report_summary()
        
        assert summary["total_reports"] >= 3
        assert summary["new_reports"] >= 3
        assert summary["by_type"]["bug"] >= 2
