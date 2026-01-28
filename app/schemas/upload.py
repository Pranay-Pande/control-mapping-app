"""
Pydantic schemas for upload operations.
"""
from pydantic import BaseModel
from typing import Optional, Any


class UploadResponse(BaseModel):
    """Response after successful file upload."""
    upload_id: str
    filename: str
    file_type: str
    size_bytes: int
    preview: Optional[str] = None

    class Config:
        from_attributes = True
