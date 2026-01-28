"""
Database models for uploads, configurations, batches, and jobs.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base
from app.models.enums import JobStatus


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Upload(Base):
    """Model for tracking uploaded files."""
    __tablename__ = "uploads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    preview = Column(Text, nullable=True)  # First 500 chars
    structure = Column(JSON, nullable=True)  # Detected structure
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    configurations = relationship("Configuration", back_populates="upload")


class Configuration(Base):
    """Model for storing mapping configurations."""
    __tablename__ = "configurations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    upload_id = Column(String(36), ForeignKey("uploads.id"), nullable=False)
    framework_name = Column(String(255), nullable=False)
    framework_version = Column(String(50), nullable=True)
    framework_full_name = Column(Text, nullable=True)  # Full descriptive name for output
    framework_description = Column(Text, nullable=True)  # Custom description for the mapping
    providers = Column(JSON, nullable=False)  # List of provider names
    enable_subgroup = Column(Boolean, default=True, nullable=False)  # Whether to include SubGroup field
    field_mappings = Column(JSON, nullable=False)
    custom_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    upload = relationship("Upload", back_populates="configurations")
    batches = relationship("Batch", back_populates="configuration")


class Batch(Base):
    """Model for tracking a batch of mapping jobs (one per provider)."""
    __tablename__ = "batches"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    configuration_id = Column(String(36), ForeignKey("configurations.id"), nullable=False)
    upload_id = Column(String(36), ForeignKey("uploads.id"), nullable=False)
    framework_name = Column(String(255), nullable=False)
    status = Column(String(20), default=JobStatus.PENDING.value, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    configuration = relationship("Configuration", back_populates="batches")
    upload = relationship("Upload")
    jobs = relationship("Job", back_populates="batch")


class Job(Base):
    """Model for tracking individual mapping jobs (one per provider)."""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    batch_id = Column(String(36), ForeignKey("batches.id"), nullable=True)
    status = Column(String(20), default=JobStatus.PENDING.value, nullable=False)

    # References
    upload_id = Column(String(36), ForeignKey("uploads.id"), nullable=False)
    configuration_id = Column(String(36), ForeignKey("configurations.id"), nullable=False)

    # Configuration snapshot (for reproducibility)
    framework_name = Column(String(255), nullable=True)
    framework_version = Column(String(50), nullable=True)
    framework_full_name = Column(Text, nullable=True)  # Full descriptive name
    provider = Column(String(50), nullable=False)  # Single provider for this job
    field_mappings = Column(JSON, nullable=True)
    custom_instructions = Column(Text, nullable=True)

    # Progress tracking
    progress_message = Column(Text, nullable=True)
    progress_percentage = Column(Integer, default=0)

    # Results
    output_json_path = Column(String(500), nullable=True)
    output_excel_path = Column(String(500), nullable=True)
    result_summary = Column(JSON, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    upload = relationship("Upload")
    configuration = relationship("Configuration")
    batch = relationship("Batch", back_populates="jobs")

    def to_dict(self) -> dict:
        """Convert job to dictionary for API response."""
        result = {
            "job_id": self.id,
            "provider": self.provider,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "progress_message": self.progress_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if self.status == JobStatus.COMPLETED.value:
            result["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
            result["summary"] = self.result_summary
            result["download_links"] = {
                "json": f"/download/{self.id}/json",
                "excel": f"/download/{self.id}/excel"
            }

        if self.status == JobStatus.FAILED.value:
            result["error_message"] = self.error_message

        return result
