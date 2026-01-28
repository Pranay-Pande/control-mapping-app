"""
Upload endpoint for compliance documents.
"""
import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import get_db_session
from app.models.job import Upload
from app.models.enums import FileType
from app.schemas.upload import UploadResponse
from app.services.file_processor import FileProcessorFactory
from app.core.exceptions import InvalidFileTypeError, FileTooLargeError

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Upload a compliance framework document.

    Supports: PDF, CSV, Excel (.xlsx, .xls), JSON, TXT
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Check file extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    # Check file size
    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_upload_size / 1024 / 1024:.1f}MB"
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Generate unique ID and save file
    upload_id = str(uuid.uuid4())
    file_path = settings.upload_dir / f"{upload_id}{suffix}"

    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    # Process file to extract text
    try:
        file_type = FileProcessorFactory.get_file_type(file_path)
        extracted_text, preview, structure = FileProcessorFactory.process_file(file_path)
    except Exception as e:
        # Clean up file if processing fails
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")

    # Create database record
    upload = Upload(
        id=upload_id,
        filename=file.filename,
        file_type=file_type.value,
        file_path=str(file_path),
        file_size=len(content),
        extracted_text=extracted_text,
        preview=preview,
        structure=structure
    )

    db.add(upload)
    await db.commit()

    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename,
        file_type=file_type.value,
        size_bytes=len(content),
        preview=preview
    )
