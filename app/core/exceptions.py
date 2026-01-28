"""
Custom exceptions for the application.
"""


class MappingError(Exception):
    """Base exception for mapping operations."""
    pass


class FileProcessingError(MappingError):
    """Raised when a file cannot be processed."""
    pass


class InvalidFileTypeError(FileProcessingError):
    """Raised when file type is not supported."""
    pass


class FileTooLargeError(FileProcessingError):
    """Raised when file exceeds size limit."""
    pass


class ClaudeExecutionError(MappingError):
    """Raised when Claude Code fails to execute."""
    pass


class ClaudeTimeoutError(ClaudeExecutionError):
    """Raised when Claude Code execution times out."""
    pass


class OutputParsingError(MappingError):
    """Raised when Claude output cannot be parsed as JSON."""
    pass


class ProviderNotFoundError(MappingError):
    """Raised when a provider doesn't exist."""
    pass


class UploadNotFoundError(MappingError):
    """Raised when an upload record is not found."""
    pass


class ConfigurationNotFoundError(MappingError):
    """Raised when a configuration record is not found."""
    pass


class JobNotFoundError(MappingError):
    """Raised when a job record is not found."""
    pass


class JobNotCompletedError(MappingError):
    """Raised when trying to download from an incomplete job."""
    pass
