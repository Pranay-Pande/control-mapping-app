"""
Enumeration types for the application.
"""
from enum import Enum


class JobStatus(str, Enum):
    """Status of a mapping job."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, Enum):
    """Supported file types for upload."""
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    JSON = "json"
    TXT = "txt"
