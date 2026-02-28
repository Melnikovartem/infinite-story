"""Content reporting endpoints."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.content_report import ContentReport, ReportType, ReportStatus

router = APIRouter()


class ContentReportRequest(BaseModel):
    """Request body for submitting a content report."""
    story_id: str = Field(..., description="ID of the story")
    segment_id: str = Field(..., description="ID of the problematic segment")
    report_type: str = Field(
        default="other",
        description="Type of issue (inappropriate_content, bug, spelling_error, plot_issue, other)"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Description of the issue"
    )
    reporter_email: Optional[EmailStr] = Field(
        None,
        description="Reporter's email (optional)"
    )


class ContentReportResponse(BaseModel):
    """Response for report submission."""
    success: bool = Field(..., description="Whether report was submitted successfully")
    report_id: str = Field(..., description="Unique report ID")
    message: str = Field(..., description="Response message")
    created_at: datetime = Field(..., description="When the report was created")


class ContentReportDetailResponse(BaseModel):
    """Response with detailed report information."""
    id: str = Field(..., description="Report ID")
    story_id: str = Field(..., description="Story ID")
    segment_id: str = Field(..., description="Segment ID")
    report_type: str = Field(..., description="Report type")
    description: str = Field(..., description="Report description")
    reporter_email: Optional[str] = Field(None, description="Reporter email")
    status: str = Field(..., description="Report status")
    created_at: datetime = Field(..., description="Creation timestamp")
    reviewed_at: Optional[datetime] = Field(None, description="Review timestamp")
    reviewer_notes: Optional[str] = Field(None, description="Reviewer notes")


class ReportListResponse(BaseModel):
    """Response for listing reports."""
    total: int = Field(..., description="Total number of reports")
    reports: List[ContentReportDetailResponse] = Field(
        ...,
        description="List of reports"
    )


class ReportSummaryResponse(BaseModel):
    """Response with report summary statistics."""
    total_reports: int = Field(..., description="Total reports")
    new_reports: int = Field(..., description="New (unreviewed) reports")
    reviewed_reports: int = Field(..., description="Reviewed reports")
    resolved_reports: int = Field(..., description="Resolved reports")
    dismissed_reports: int = Field(..., description="Dismissed reports")
    by_type: dict = Field(..., description="Report counts by type")


@router.post("/reports", response_model=ContentReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(request: ContentReportRequest) -> ContentReportResponse:
    """Submit a content report.
    
    Args:
        request: Report details
        
    Returns:
        Success response with report ID
    """
    try:
        # Convert report type string to enum
        try:
            report_type = ReportType(request.report_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report_type. Must be one of: {', '.join([rt.value for rt in ReportType])}"
            )
        
        # Create report
        report = ContentReport(
            story_id=request.story_id,
            segment_id=request.segment_id,
            report_type=report_type,
            description=request.description,
            reporter_email=request.reporter_email
        )
        
        # Save to disk
        ContentReport.save_to_file(report)
        
        return ContentReportResponse(
            success=True,
            report_id=report.id,
            message="Thank you for your report. We will review it shortly.",
            created_at=report.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to submit report: {str(e)}"
        )


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    story_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    report_type: Optional[str] = None
) -> ReportListResponse:
    """List all reports with optional filters.
    
    Args:
        story_id: Filter by story ID
        status_filter: Filter by status (new, reviewed, resolved, dismissed)
        report_type: Filter by report type
        
    Returns:
        List of reports matching filters
    """
    try:
        reports = []
        
        # Get all reports
        for report_id in ContentReport.list_all():
            report = ContentReport.load_from_file(report_id)
            if report is None:
                continue
            
            # Apply filters
            if story_id and report.story_id != story_id:
                continue
            if status_filter:
                try:
                    status_enum = ReportStatus(status_filter)
                    if report.status != status_enum:
                        continue
                except ValueError:
                    pass
            if report_type:
                try:
                    type_enum = ReportType(report_type)
                    if report.report_type != type_enum:
                        continue
                except ValueError:
                    pass
            
            reports.append(report)
        
        # Convert to response format
        report_details = [
            ContentReportDetailResponse(
                id=r.id,
                story_id=r.story_id,
                segment_id=r.segment_id,
                report_type=r.report_type.value,
                description=r.description,
                reporter_email=r.reporter_email,
                status=r.status.value,
                created_at=r.created_at,
                reviewed_at=r.reviewed_at,
                reviewer_notes=r.reviewer_notes
            )
            for r in reports
        ]
        
        return ReportListResponse(
            total=len(report_details),
            reports=report_details
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}"
        )


@router.get("/reports/{report_id}", response_model=ContentReportDetailResponse)
async def get_report(report_id: str) -> ContentReportDetailResponse:
    """Get a specific report.
    
    Args:
        report_id: ID of the report
        
    Returns:
        Report details
    """
    try:
        report = ContentReport.load_from_file(report_id)
        
        if report is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        return ContentReportDetailResponse(
            id=report.id,
            story_id=report.story_id,
            segment_id=report.segment_id,
            report_type=report.report_type.value,
            description=report.description,
            reporter_email=report.reporter_email,
            status=report.status.value,
            created_at=report.created_at,
            reviewed_at=report.reviewed_at,
            reviewer_notes=report.reviewer_notes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}"
        )


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete a report.
    
    Args:
        report_id: ID of the report to delete
        
    Returns:
        Success response
    """
    try:
        deleted = ContentReport.delete_from_file(report_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report {report_id} not found"
            )
        
        return {"success": True, "message": "Report deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}"
        )


@router.get("/reports/summary/stats", response_model=ReportSummaryResponse)
async def get_report_summary() -> ReportSummaryResponse:
    """Get summary statistics about all reports.
    
    Returns:
        Report summary with counts by status and type
    """
    try:
        summary = ContentReport.get_report_summary()
        
        return ReportSummaryResponse(
            total_reports=summary["total_reports"],
            new_reports=summary["new_reports"],
            reviewed_reports=summary["reviewed_reports"],
            resolved_reports=summary["resolved_reports"],
            dismissed_reports=summary["dismissed_reports"],
            by_type={k.value: v for k, v in summary["by_type"].items()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report summary: {str(e)}"
        )
