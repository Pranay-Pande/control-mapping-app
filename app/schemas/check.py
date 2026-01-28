"""
Pydantic schemas for provider and check operations.
"""
from pydantic import BaseModel
from typing import Optional, List


class ProviderInfo(BaseModel):
    """Information about a cloud provider."""
    name: str
    display_name: str
    check_count: int


class ProvidersResponse(BaseModel):
    """Response listing all providers."""
    providers: List[ProviderInfo]


class CheckInfo(BaseModel):
    """Information about a security check."""
    CheckID: str
    CheckTitle: str
    ServiceName: Optional[str] = None
    Severity: Optional[str] = None
    Description: Optional[str] = None


class ChecksResponse(BaseModel):
    """Response listing checks for a provider."""
    provider: str
    total: int
    checks: List[CheckInfo]
