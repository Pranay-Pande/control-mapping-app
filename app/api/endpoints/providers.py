"""
Provider and check listing endpoints.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.check import (
    ProvidersResponse,
    ProviderInfo,
    ChecksResponse,
    CheckInfo
)
from app.services.check_repository import get_check_repository

router = APIRouter()


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers():
    """
    List all available cloud providers.
    """
    check_repo = get_check_repository()
    providers = check_repo.list_providers()

    return ProvidersResponse(
        providers=[
            ProviderInfo(
                name=p["name"],
                display_name=p["display_name"],
                check_count=p["check_count"]
            )
            for p in providers
        ]
    )


@router.get("/checks/{provider}", response_model=ChecksResponse)
async def list_checks(
    provider: str,
    search: Optional[str] = Query(None, description="Search in check name/description"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List security checks for a provider.
    """
    check_repo = get_check_repository()

    # Verify provider exists
    if not check_repo.provider_exists(provider):
        providers = check_repo.list_providers()
        provider_names = [p["name"] for p in providers]
        raise HTTPException(
            status_code=404,
            detail=f"Provider '{provider}' not found. Available: {', '.join(provider_names)}"
        )

    # Get checks
    total, checks = check_repo.get_checks(
        provider=provider,
        search=search,
        service=service,
        limit=limit,
        offset=offset
    )

    return ChecksResponse(
        provider=provider,
        total=total,
        checks=[
            CheckInfo(
                CheckID=c.get("CheckID", ""),
                CheckTitle=c.get("CheckTitle", ""),
                ServiceName=c.get("ServiceName"),
                Severity=c.get("Severity"),
                Description=c.get("Description")
            )
            for c in checks
        ]
    )
