"""
Pydantic schemas for mapping operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class MapRequest(BaseModel):
    """Request to start a mapping job."""
    upload_id: str = Field(..., description="UUID of the uploaded file")
    configuration_id: str = Field(..., description="UUID of the configuration")


class JobInfo(BaseModel):
    """Basic info about a job in a batch."""
    job_id: str
    provider: str
    status: str


class MapResponse(BaseModel):
    """Response after starting a batch of mapping jobs."""
    batch_id: str
    job_ids: List[str]
    jobs: List[JobInfo]
    created_at: datetime

    class Config:
        from_attributes = True


class JobSummary(BaseModel):
    """Summary of a completed job."""
    total_controls: int
    controls_with_checks: int
    total_check_mappings: int
    unmapped_controls: int


class DownloadLinks(BaseModel):
    """Links to download job outputs."""
    json: str
    excel: str


class JobStatusResponse(BaseModel):
    """Response for individual job status query."""
    job_id: str
    provider: str
    status: str
    progress_percentage: int
    progress_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    summary: Optional[JobSummary] = None
    download_links: Optional[DownloadLinks] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class BatchJobStatus(BaseModel):
    """Status of an individual job within a batch."""
    job_id: str
    provider: str
    status: str
    progress_percentage: int
    progress_message: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BatchStatusResponse(BaseModel):
    """Response for batch status query."""
    batch_id: str
    status: str  # pending, running, completed, failed, partial
    overall_progress: int
    current_message: Optional[str] = None
    jobs: List[BatchJobStatus]
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
