"""
Mapping endpoints for starting jobs and checking status.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import get_db_session
from app.models.job import Job, Batch, Upload, Configuration
from app.models.enums import JobStatus
from app.schemas.mapping import (
    MapRequest, MapResponse, JobInfo,
    JobStatusResponse, BatchStatusResponse, BatchJobStatus
)
from app.core.job_manager import get_job_manager

router = APIRouter()


@router.post("/map", response_model=MapResponse, status_code=202)
async def start_mapping(
    request: MapRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start mapping jobs for all configured providers.

    Creates a batch with one job per provider. Jobs run asynchronously.
    Use GET /batch/{batch_id}/status to check progress.
    """
    # Verify upload exists
    upload = await db.get(Upload, request.upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    # Verify configuration exists
    config = await db.get(Configuration, request.configuration_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")

    # Verify configuration matches upload
    if config.upload_id != request.upload_id:
        raise HTTPException(
            status_code=400,
            detail="Configuration does not match upload"
        )

    # Create batch record
    batch = Batch(
        configuration_id=request.configuration_id,
        upload_id=request.upload_id,
        framework_name=config.framework_name,
        status=JobStatus.PENDING.value
    )
    db.add(batch)
    await db.flush()  # Get batch ID

    # Create a job for each provider
    jobs = []
    job_ids = []
    job_infos = []

    for provider in config.providers:
        job = Job(
            batch_id=batch.id,
            upload_id=request.upload_id,
            configuration_id=request.configuration_id,
            framework_name=config.framework_name,
            framework_version=config.framework_version,
            framework_full_name=config.framework_full_name,
            provider=provider,
            field_mappings=config.field_mappings,
            custom_instructions=config.custom_instructions,
            status=JobStatus.PENDING.value,
            progress_message="Job queued..."
        )
        db.add(job)
        jobs.append(job)

    await db.commit()

    # Refresh to get IDs
    for job in jobs:
        await db.refresh(job)
        job_ids.append(job.id)
        job_infos.append(JobInfo(
            job_id=job.id,
            provider=job.provider,
            status=job.status
        ))

    # Start all jobs in the background
    job_manager = get_job_manager()
    await job_manager.start_batch(batch.id, job_ids)

    return MapResponse(
        batch_id=batch.id,
        job_ids=job_ids,
        jobs=job_infos,
        created_at=batch.created_at
    )


@router.get("/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(
    batch_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the status of a batch of mapping jobs.
    """
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get all jobs in this batch
    result = await db.execute(
        select(Job).where(Job.batch_id == batch_id)
    )
    jobs = result.scalars().all()

    # Calculate overall progress and status
    total_progress = 0
    completed_count = 0
    failed_count = 0
    running_count = 0
    current_message = None

    job_statuses = []
    for job in jobs:
        total_progress += job.progress_percentage or 0

        if job.status == JobStatus.COMPLETED.value:
            completed_count += 1
        elif job.status == JobStatus.FAILED.value:
            failed_count += 1
        elif job.status == JobStatus.RUNNING.value:
            running_count += 1
            current_message = f"Processing {job.provider}: {job.progress_message or ''}"

        job_statuses.append(BatchJobStatus(
            job_id=job.id,
            provider=job.provider,
            status=job.status,
            progress_percentage=job.progress_percentage or 0,
            progress_message=job.progress_message,
            summary=job.result_summary,
            error_message=job.error_message
        ))

    # Calculate overall progress percentage
    overall_progress = total_progress // len(jobs) if jobs else 0

    # Determine batch status
    if completed_count == len(jobs):
        batch_status = "completed"
    elif failed_count == len(jobs):
        batch_status = "failed"
    elif failed_count > 0 and completed_count + failed_count == len(jobs):
        batch_status = "partial"  # Some completed, some failed
    elif running_count > 0 or completed_count > 0:
        batch_status = "running"
    else:
        batch_status = "pending"

    return BatchStatusResponse(
        batch_id=batch.id,
        status=batch_status,
        overall_progress=overall_progress,
        current_message=current_message,
        jobs=job_statuses,
        created_at=batch.created_at.isoformat() if batch.created_at else None,
        completed_at=batch.completed_at.isoformat() if batch.completed_at else None
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the status of an individual mapping job.
    """
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = JobStatusResponse(
        job_id=job.id,
        provider=job.provider,
        status=job.status,
        progress_percentage=job.progress_percentage or 0,
        progress_message=job.progress_message,
        created_at=job.created_at.isoformat() if job.created_at else None,
        updated_at=job.updated_at.isoformat() if job.updated_at else None
    )

    if job.status == JobStatus.COMPLETED.value:
        response.completed_at = job.completed_at.isoformat() if job.completed_at else None
        if job.result_summary:
            response.summary = job.result_summary
        response.download_links = {
            "json": f"/download/{job.id}/json",
            "excel": f"/download/{job.id}/excel"
        }

    if job.status == JobStatus.FAILED.value:
        response.error_message = job.error_message

    return response
