"""
Download endpoint for mapping outputs.
"""
import io
import zipfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db_session
from app.models.job import Job, Batch
from app.models.enums import JobStatus

router = APIRouter()


@router.get("/download/{job_id}/{file_type}")
async def download_output(
    job_id: str,
    file_type: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Download the mapping output file.

    Args:
        job_id: UUID of the completed job
        file_type: Either 'json' or 'excel'
    """
    # Validate file type
    if file_type not in ("json", "excel"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Use 'json' or 'excel'"
        )

    # Get job
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Check job is completed
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed. Current status: {job.status}"
        )

    # Get the appropriate file path
    if file_type == "json":
        file_path = job.output_json_path
        media_type = "application/json"
        filename = f"{job.framework_name or 'mapping'}_{job.provider}.json"
    else:
        file_path = job.output_excel_path
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{job.framework_name or 'mapping'}_{job.provider}.xlsx"

    # Verify file exists
    if not file_path:
        raise HTTPException(status_code=404, detail=f"Output file not found")

    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file not found on disk")

    # Clean filename for download
    filename = filename.replace(" ", "_").replace("/", "_")

    return FileResponse(
        path=path,
        media_type=media_type,
        filename=filename
    )


@router.get("/download/batch/{batch_id}/zip")
async def download_batch_zip(
    batch_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Download all completed job outputs as a ZIP file.

    Args:
        batch_id: UUID of the batch
    """
    # Get batch
    batch = await db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get all completed jobs in this batch
    result = await db.execute(
        select(Job).where(
            Job.batch_id == batch_id,
            Job.status == JobStatus.COMPLETED.value
        )
    )
    jobs = result.scalars().all()

    if not jobs:
        raise HTTPException(
            status_code=400,
            detail="No completed jobs found in this batch"
        )

    # Create ZIP file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for job in jobs:
            framework_name = job.framework_name or 'mapping'
            provider = job.provider

            # Add JSON file if exists
            if job.output_json_path:
                json_path = Path(job.output_json_path)
                if json_path.exists():
                    json_filename = f"{framework_name}_{provider}.json".replace(" ", "_")
                    zip_file.write(json_path, json_filename)

            # Add Excel file if exists
            if job.output_excel_path:
                excel_path = Path(job.output_excel_path)
                if excel_path.exists():
                    excel_filename = f"{framework_name}_{provider}.xlsx".replace(" ", "_")
                    zip_file.write(excel_path, excel_filename)

    # Prepare response
    zip_buffer.seek(0)
    zip_filename = f"{batch.framework_name or 'mapping'}_all_providers.zip".replace(" ", "_")

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={zip_filename}"
        }
    )
