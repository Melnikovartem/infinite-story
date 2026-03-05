"""Content reporting models for moderation system."""

import uuid
import json
from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr


class ReportType(str, Enum):
    """Types of content reports."""
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    BUG = "bug"
    SPELLING_ERROR = "spelling_error"
    PLOT_ISSUE = "plot_issue"
    OTHER = "other"


class ReportStatus(str, Enum):
    """Status of a report."""
    NEW = "new"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ContentReport(BaseModel):
    """Report of inappropriate or problematic content.
    
    Allows players to flag content for moderation review.
    """
    
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique report ID"
    )
    story_id: str = Field(..., description="ID of the story")
    segment_id: str = Field(..., description="ID of the segment with the issue")
    report_type: ReportType = Field(
        default=ReportType.OTHER,
        description="Type of issue being reported"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of the issue"
    )
    reporter_email: Optional[EmailStr] = Field(
        default=None,
        description="Email of the reporter (optional)"
    )
    status: ReportStatus = Field(
        default=ReportStatus.NEW,
        description="Current status of the report"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the report was created"
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
        description="When the report was reviewed"
    )
    reviewer_notes: Optional[str] = Field(
        default=None,
        description="Notes from reviewer"
    )
    
    def mark_reviewed(self, notes: Optional[str] = None) -> None:
        """Mark this report as reviewed.
        
        Args:
            notes: Optional reviewer notes
        """
        self.status = ReportStatus.REVIEWED
        self.reviewed_at = datetime.now(UTC)
        if notes:
            self.reviewer_notes = notes
    
    def resolve(self, notes: Optional[str] = None) -> None:
        """Mark this report as resolved.
        
        Args:
            notes: Optional resolution notes
        """
        self.status = ReportStatus.RESOLVED
        self.reviewed_at = datetime.now(UTC)
        if notes:
            self.reviewer_notes = notes
    
    def dismiss(self, notes: Optional[str] = None) -> None:
        """Mark this report as dismissed.
        
        Args:
            notes: Optional dismissal reason
        """
        self.status = ReportStatus.DISMISSED
        self.reviewed_at = datetime.now(UTC)
        if notes:
            self.reviewer_notes = notes
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return self.model_dump(mode='json')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ContentReport':
        """Create from dictionary.
        
        Args:
            data: Dictionary containing report data
            
        Returns:
            ContentReport instance
        """
        return cls(**data)
    
    @classmethod
    def save_to_file(cls, report: 'ContentReport') -> Path:
        """Save report to disk as JSON file.
        
        Args:
            report: ContentReport instance to save
            
        Returns:
            Path where the report was saved
        """
        # Create directory structure: .infinite_story_data/reports/
        reports_dir = Path(".infinite_story_data") / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with report ID as filename
        file_path = reports_dir / f"{report.id}.json"
        with open(file_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        
        return file_path
    
    @classmethod
    def load_from_file(cls, report_id: str) -> Optional['ContentReport']:
        """Load report from disk JSON file.
        
        Args:
            report_id: ID of the report to load
            
        Returns:
            ContentReport instance if found, None otherwise
        """
        file_path = Path(".infinite_story_data") / "reports" / f"{report_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load report from {file_path}: {e}")
            return None
    
    @classmethod
    def delete_from_file(cls, report_id: str) -> bool:
        """Delete report from disk.
        
        Args:
            report_id: ID of the report to delete
            
        Returns:
            True if deleted, False if it didn't exist
        """
        file_path = Path(".infinite_story_data") / "reports" / f"{report_id}.json"
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    @classmethod
    def list_all(cls) -> List[str]:
        """List all report IDs.
        
        Returns:
            List of report IDs
        """
        reports_dir = Path(".infinite_story_data") / "reports"
        
        if not reports_dir.exists():
            return []
        
        return [f.stem for f in reports_dir.glob("*.json")]
    
    @classmethod
    def list_by_story(cls, story_id: str) -> List['ContentReport']:
        """List all reports for a specific story.
        
        Args:
            story_id: ID of the story
            
        Returns:
            List of ContentReport instances for that story
        """
        reports = []
        for report_id in cls.list_all():
            report = cls.load_from_file(report_id)
            if report and report.story_id == story_id:
                reports.append(report)
        
        return sorted(reports, key=lambda r: r.created_at, reverse=True)
    
    @classmethod
    def list_by_status(cls, status: ReportStatus) -> List['ContentReport']:
        """List all reports with a specific status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of ContentReport instances with that status
        """
        reports = []
        for report_id in cls.list_all():
            report = cls.load_from_file(report_id)
            if report and report.status == status:
                reports.append(report)
        
        return sorted(reports, key=lambda r: r.created_at, reverse=True)
    
    @classmethod
    def list_by_type(cls, report_type: ReportType) -> List['ContentReport']:
        """List all reports of a specific type.
        
        Args:
            report_type: Type to filter by
            
        Returns:
            List of ContentReport instances of that type
        """
        reports = []
        for report_id in cls.list_all():
            report = cls.load_from_file(report_id)
            if report and report.report_type == report_type:
                reports.append(report)
        
        return sorted(reports, key=lambda r: r.created_at, reverse=True)
    
    @classmethod
    def get_report_summary(cls) -> dict:
        """Get summary statistics about all reports.
        
        Returns:
            Dictionary with report statistics
        """
        all_reports = [cls.load_from_file(rid) for rid in cls.list_all()]
        all_reports = [r for r in all_reports if r is not None]
        
        return {
            "total_reports": len(all_reports),
            "new_reports": len([r for r in all_reports if r.status == ReportStatus.NEW]),
            "reviewed_reports": len([r for r in all_reports if r.status == ReportStatus.REVIEWED]),
            "resolved_reports": len([r for r in all_reports if r.status == ReportStatus.RESOLVED]),
            "dismissed_reports": len([r for r in all_reports if r.status == ReportStatus.DISMISSED]),
            "by_type": {
                report_type: len([r for r in all_reports if r.report_type == report_type])
                for report_type in ReportType
            }
        }
